/*!
 * houdini-reader.js — read Houdini scene files (.hip / .hipnc / .hiplc) in the browser.
 *
 * Plain JavaScript, no dependencies, no build step, no Node.js APIs.
 * Exposes a single global: window.HoudiniReader
 *
 * Background
 * ----------
 * A Houdini scene file is a CPIO archive (usually "odc" / 070707 flavour) of small ASCII
 * files, one set per node, e.g.
 *
 *     obj/geo1.init          node type
 *     obj/geo1.def           position, flags, comment, colour, input connections, stat
 *     obj/geo1.parm          parameter values
 *     obj/geo1.chn           animation channels (expressions / keyframes)
 *     obj/geo1.userdata      user data
 *     obj/geo1/box1.init     child node ...
 *
 * The node hierarchy is simply the path structure of the archive.
 *
 * Important: Houdini only stores parameters whose values differ from the node type's
 * defaults, so `node.parms` lists only the *non-default* parameters.
 *
 * Usage
 * -----
 *     const hip = await HoudiniReader.fromFile(fileInput.files[0]);
 *     console.log(hip.houdiniVersion);
 *     hip.walk(n => console.log(n.path, n.type));
 *     const box = hip.getNode('/obj/geo1/box1');
 *     console.log(box.parm('size').value);      // e.g. [1, 2, 1]
 *     console.log(box.inputs);                  // connections
 *     console.log(hip.treeString());
 */
(function (global) {
  'use strict';

  // ---------------------------------------------------------------------------
  // Binary helpers
  // ---------------------------------------------------------------------------

  var utf8 = new TextDecoder('utf-8');

  function asciiSlice(u8, s, e) {
    var r = '';
    for (var i = s; i < e; i++) r += String.fromCharCode(u8[i]);
    return r;
  }

  async function maybeGunzip(buf) {
    var u8 = new Uint8Array(buf);
    if (u8.length > 2 && u8[0] === 0x1f && u8[1] === 0x8b) {
      if (typeof DecompressionStream === 'undefined') {
        throw new Error('File is gzip-compressed and this browser lacks DecompressionStream.');
      }
      var stream = new Blob([u8]).stream().pipeThrough(new DecompressionStream('gzip'));
      return await new Response(stream).arrayBuffer();
    }
    return buf;
  }

  /**
   * Parse a CPIO archive (odc "070707", newc "070701", crc "070702").
   * Returns [{name, mode, mtime, isDir, data(Uint8Array)}].
   */
  function parseCpio(buf) {
    var u8 = new Uint8Array(buf);
    var entries = [];
    var pos = 0;
    var align4 = function (n) { return (n + 3) & ~3; };

    while (pos + 6 <= u8.length) {
      var magic = asciiSlice(u8, pos, pos + 6);
      var name, size, mode, mtime, dataStart, next;

      if (magic === '070707') {
        if (pos + 76 > u8.length) break;
        mode = parseInt(asciiSlice(u8, pos + 18, pos + 24), 8);
        mtime = parseInt(asciiSlice(u8, pos + 48, pos + 59), 8);
        var nsO = parseInt(asciiSlice(u8, pos + 59, pos + 65), 8);
        size = parseInt(asciiSlice(u8, pos + 65, pos + 76), 8);
        if (isNaN(nsO) || isNaN(size)) throw new Error('Corrupt CPIO header at offset ' + pos);
        name = utf8.decode(u8.subarray(pos + 76, pos + 76 + nsO - 1));
        dataStart = pos + 76 + nsO;
        next = dataStart + size;
      } else if (magic === '070701' || magic === '070702') {
        if (pos + 110 > u8.length) break;
        var f = function (k) { return parseInt(asciiSlice(u8, pos + 6 + 8 * k, pos + 14 + 8 * k), 16); };
        mode = f(1); mtime = f(5); size = f(6);
        var nsN = f(11);
        if (isNaN(nsN) || isNaN(size)) throw new Error('Corrupt CPIO header at offset ' + pos);
        name = utf8.decode(u8.subarray(pos + 110, pos + 110 + nsN - 1));
        dataStart = align4(pos + 110 + nsN);
        next = align4(dataStart + size);
      } else {
        if (entries.length === 0) {
          throw new Error('Not a CPIO-based Houdini file (unknown magic "' + magic + '").');
        }
        break;
      }

      if (name === 'TRAILER!!!') break;
      name = name.replace(/^(\.\/)+/, '');
      entries.push({
        name: name,
        mode: mode,
        mtime: mtime,
        isDir: (mode & 0xF000) === 0x4000,
        data: u8.subarray(dataStart, dataStart + size)
      });
      pos = next;
    }
    return entries;
  }

  // ---------------------------------------------------------------------------
  // Text tokenizer / parsers for Houdini's ASCII sub-files
  // ---------------------------------------------------------------------------

  var NUM_RE = /^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/;
  var WORD_STOP = ' \t\r\n{}[]()"\'';

  function tokenize(text) {
    var toks = [], n = text.length, i = 0;
    while (i < n) {
      var c = text.charAt(i);
      if (c === '\n') { toks.push({ t: 'nl' }); i++; continue; }
      if (c === ' ' || c === '\t' || c === '\r') { i++; continue; }
      if ('{}[]()'.indexOf(c) >= 0) { toks.push({ t: c }); i++; continue; }
      if (c === '"' || c === "'") {
        var j = i + 1, s = '';
        while (j < n && text.charAt(j) !== c) {
          if (text.charAt(j) === '\\' && j + 1 < n) {
            var d = text.charAt(j + 1);
            if (d === 'n') s += '\n';
            else if (d === 't') s += '\t';
            else if (d === '"' || d === "'" || d === '\\') s += d;
            else s += '\\' + d;
            j += 2;
          } else { s += text.charAt(j); j++; }
        }
        toks.push({ t: 'str', v: s });
        i = j + 1;
        continue;
      }
      var k = i;
      while (k < n && WORD_STOP.indexOf(text.charAt(k)) < 0) k++;
      toks.push({ t: 'word', v: text.slice(i, k) });
      i = k;
    }
    return toks;
  }

  function tokVal(t) { return t.v !== undefined ? t.v : t.t; }

  /**
   * Generic statement/block parser used for .def, .chn, .userdata:
   *   key arg arg ...
   *   key arg ... { children }      (the "{" may be on the following line)
   * Returns [{key, args:[string], children:[...]|null}]
   */
  function parseStatements(toks, start, depth) {
    var out = [], i = start || 0;
    while (i < toks.length) {
      var t = toks[i];
      if (t.t === 'nl') { i++; continue; }
      if (t.t === '}') {
        if (depth > 0) return { stmts: out, next: i + 1 };
        i++; continue;
      }
      var r;
      if (t.t === '{') {
        r = parseStatements(toks, i + 1, depth + 1);
        out.push({ key: '', args: [], children: r.stmts });
        i = r.next;
        continue;
      }
      var key = tokVal(t), args = [], children = null;
      i++;
      while (i < toks.length && toks[i].t !== 'nl' && toks[i].t !== '{' && toks[i].t !== '}') {
        args.push(tokVal(toks[i])); i++;
      }
      if (i < toks.length && toks[i].t === '{') {
        r = parseStatements(toks, i + 1, depth + 1);
        children = r.stmts; i = r.next;
      } else if (i < toks.length && toks[i].t === 'nl') {
        var j = i;
        while (j < toks.length && toks[j].t === 'nl') j++;
        if (j < toks.length && toks[j].t === '{') {
          r = parseStatements(toks, j + 1, depth + 1);
          children = r.stmts; i = r.next;
        }
      }
      out.push({ key: key, args: args, children: children });
    }
    return { stmts: out, next: i };
  }

  function parseBlocks(text) { return parseStatements(tokenize(text), 0, 0).stmts; }

  function autoNum(s) { return (typeof s === 'string' && NUM_RE.test(s)) ? Number(s) : s; }

  /** Re-join function calls split by the tokenizer: bezier ( ) -> bezier() */
  function mergeCalls(vals) {
    var out = [], open = 0;
    vals.forEach(function (v) {
      if (v === '(' && out.length) { out[out.length - 1] += '('; open++; }
      else if (v === ')' && out.length) { out[out.length - 1] += ')'; open = Math.max(0, open - 1); }
      else if (open && out.length) { var l = out[out.length - 1]; out[out.length - 1] = l + (/[(,]$/.test(l) ? '' : ' ') + v; }
      else out.push(v);
    });
    return out;
  }

  /** "a = 1 2  b = x" -> {a:[1,2], b:'x'} */
  function kvFromTokens(tokens) {
    var res = {}, cur = null;
    for (var i = 0; i < tokens.length; i++) {
      if (tokens[i + 1] === '=' && tokens[i] !== '=') { cur = tokens[i]; res[cur] = []; i++; }
      else if (cur !== null) res[cur].push(tokens[i]);
    }
    Object.keys(res).forEach(function (k) {
      var v = mergeCalls(res[k]).map(autoNum);
      res[k] = v.length === 1 ? v[0] : v;
    });
    return res;
  }

  function flattenStmtTokens(stmts) {
    var toks = [];
    (stmts || []).forEach(function (s) { toks.push(s.key); toks.push.apply(toks, s.args); });
    return toks;
  }

  /** "type = geo" style files (.init) */
  function parseKeyValueLines(text) {
    var res = {};
    text.split(/\r?\n/).forEach(function (line) {
      var m = /^\s*([^\s=]+)\s*=\s*(.*?)\s*$/.exec(line);
      if (!m) return;
      var v = m[2];
      if (/^".*"$/.test(v) || /^'.*'$/.test(v)) v = v.slice(1, -1);
      res[m[1]] = v;
    });
    return res;
  }

  function convertItem(it) {
    if (it.group) {
      return { type: 'group', value: it.group.map(convertItem), raw: it.group.map(tokVal2) };
    }
    if (it.t === 'str') return { type: 'string', value: it.v };
    if (NUM_RE.test(it.v)) return { type: 'number', value: Number(it.v) };
    return { type: 'word', value: it.v };
  }
  function tokVal2(it) { return it.group ? it.group.map(tokVal2) : tokVal(it); }

  function readGroup(toks, i) {
    var kind = toks[i].t;
    var close = kind === '[' ? ']' : ')';
    i++;
    var items = [];
    while (i < toks.length && toks[i].t !== close) {
      var t = toks[i];
      if (t.t === 'nl' || t.t === '{' || t.t === '}') { i++; continue; }
      if (t.t === '[' || t.t === '(') {
        var r = readGroup(toks, i);
        items.push({ group: r.items, kind: t.t });
        i = r.next;
        continue;
      }
      items.push(t); i++;
    }
    return { items: items, next: i + 1 };
  }

  /**
   * Parse a .parm file:
   *   name [ flags locks=0 ] ( v1 v2 ... )
   * Returns { meta:{version:..}, parms:[Parm] }
   */
  function parseParmFile(text) {
    var toks = tokenize(text), i = 0, parms = [], meta = {};
    while (i < toks.length) {
      var tk = toks[i];
      if (tk.t === 'nl' || tk.t === '{' || tk.t === '}') { i++; continue; }
      var name = tokVal(tk); i++;
      var flagsGroup = null, valGroup = null, extra = [];
      while (i < toks.length && toks[i].t !== 'nl' && toks[i].t !== '{' && toks[i].t !== '}') {
        var t = toks[i];
        if (t.t === '[' || t.t === '(') {
          var g = readGroup(toks, i);
          if (t.t === '[' && !flagsGroup && !valGroup) flagsGroup = g.items;
          else if (t.t === '(' && !valGroup) valGroup = g.items;
          else extra.push({ group: g.items });
          i = g.next;
        } else { extra.push(t); i++; }
      }
      if (!valGroup) { meta[name] = extra.map(function (e) { return e.group ? tokVal2(e) : tokVal(e); }); continue; }

      var flagWords = (flagsGroup || []).map(tokVal2);
      var locks = null;
      flagWords.forEach(function (w) {
        var m = typeof w === 'string' && /^locks=(.*)$/.exec(w);
        if (m) locks = autoNum(m[1]);
      });
      var values = valGroup.map(convertItem);
      parms.push({
        name: name,
        flags: flagWords,
        locks: locks,
        values: values,
        size: values.length,
        value: values.length === 1 ? values[0].value : values.map(function (v) { return v.value; }),
        channels: null // filled in later from .chn
      });
    }
    return { meta: meta, parms: parms };
  }

  /** .chn -> { channelName: { attrs:{}, segments:[{...}], keys:[] } }  (best effort)
   *  Accepts both "channel NAME { ... }" and "NAME { ... }" block styles. */
  function parseChannels(text) {
    var channels = {};
    function visit(stmts) {
      stmts.forEach(function (s) {
        var kids = s.children || [];
        var isCh = s.key === 'channel' ? s.args.length > 0
          : kids.some(function (c) { return c.key === 'segment' || c.key === 'lefttype' || c.key === 'righttype'; });
        if (isCh) {
          var ch = { attrs: {}, segments: [], keys: [] };
          var plain = [];
          kids.forEach(function (c) {
            if (c.key === 'segment') {
              ch.segments.push(kvFromTokens(c.children ? flattenStmtTokens(c.children) : c.args));
            } else plain.push(c);
          });
          ch.attrs = kvFromTokens(flattenStmtTokens(plain));
          channels[s.key === 'channel' ? s.args[0] : s.key] = ch;
        } else if (kids.length) visit(kids);
      });
    }
    visit(parseBlocks(text));
    return channels;
  }

  /** Derive absolute key times/frames from segment lengths.
   *  Each segment ends at a key; `length` is the time (seconds) since the previous key. */
  function annotateChannel(ch, fps) {
    var t = 0;
    ch.fps = fps;
    ch.keys = ch.segments.map(function (seg, i) {
      var len = Number(seg.length) || 0;
      t += len;
      var k = { index: i, time: t, frame: t * fps + 1, length: len };
      Object.keys(seg).forEach(function (key) { if (key !== 'length') k[key] = seg[key]; });
      return k;
    });
  }

  /** .def -> position, flags, comment, color, stat, input list (names unresolved) */
  function parseDef(text) {
    var stmts = parseBlocks(text);
    var top = (stmts.length === 1 && stmts[0].key === '' && stmts[0].children) ? stmts[0].children : stmts;
    var def = { position: null, flags: {}, comment: '', color: null, stat: {}, inputs: [], other: {}, raw: top };
    var inputsSrc = {};
    top.forEach(function (s) {
      switch (s.key) {
        case 'position':
          def.position = s.args.map(Number); break;
        case 'comment':
          def.comment = s.args.length ? s.args[0] : ''; break;
        case 'flags': {
          var a = s.args.slice(); if (a[0] === '=') a.shift();
          for (var i = 0; i + 1 < a.length; i += 2) def.flags[a[i]] = (a[i + 1] === 'on');
          break;
        }
        case 'color':
          def.color = s.args.map(autoNum); break;
        case 'stat': {
          // child statements look like "create 1234567890", "author user@host"
          (s.children || []).forEach(function (c) { def.stat[c.key] = autoNum(c.args[0]); });
          if (def.stat.create) def.stat.createDate = new Date(def.stat.create * 1000);
          if (def.stat.modify) def.stat.modifyDate = new Date(def.stat.modify * 1000);
          break;
        }
        case 'inputs':
        case 'inputsNamed2':
        case 'inputsNamed3':
          inputsSrc[s.key] = s.children || []; break;
        case 'end':
        case 'exprlanguage':
          break;
        default:
          if (!s.key) break;
          def.other[s.key] = s.children
            ? { args: s.args, lines: s.children.map(function (c) { return [c.key].concat(c.args).join(' '); }) }
            : s.args;
      }
    });
    var chosen = inputsSrc.inputsNamed3 || inputsSrc.inputsNamed2 || inputsSrc.inputs || [];
    chosen.forEach(function (c) {
      var idx = parseInt(c.key, 10);
      if (isNaN(idx) || !c.args.length) return;
      def.inputs.push({
        index: idx,
        sourceName: c.args[0],
        outputIndex: c.args.length > 1 ? Number(c.args[1]) || 0 : 0
      });
    });
    return def;
  }

  /** .userdata -> {key: value} (best effort) */
  function parseUserData(text) {
    var res = {};
    (function visit(stmts) {
      stmts.forEach(function (s) {
        if (s.key && s.key !== '___Version___') {
          var a = s.args.filter(function (x) { return x !== '='; });
          res[s.key] = a.join(' ');
        }
        if (s.children) visit(s.children);
      });
    })(parseBlocks(text));
    return res;
  }

  /** .variables -> {NAME: value} from lines like:  set -g NAME = 'value' */
  function parseVariables(text) {
    var res = {};
    text.split(/\r?\n/).forEach(function (line) {
      var m = /^\s*set\s+-g\s+(\S+)\s*=\s*(.*?)\s*$/.exec(line);
      if (!m) return;
      var v = m[2];
      if (/^'.*'$/.test(v) || /^".*"$/.test(v)) v = v.slice(1, -1);
      res[m[1]] = v;
    });
    return res;
  }

  // ---------------------------------------------------------------------------
  // Node model
  // ---------------------------------------------------------------------------

  function HNode(name, parent) {
    this.name = name;
    this.parent = parent || null;
    this.children = [];
    this._childMap = Object.create(null);
    this.files = {};             // extension -> Uint8Array (raw sub-files)
    this.type = null;            // e.g. "geo", "box", "merge"
    this.init = {};              // everything in .init
    this.parms = [];             // non-default parameters
    this.parmMeta = {};
    this.position = null;        // [x, y] in the network editor
    this.flags = {};             // {display:true, render:true, bypass:false ...}
    this.comment = '';
    this.color = null;
    this.stat = {};              // create/modify/author/access
    this.inputs = [];            // [{index, sourceName, outputIndex, node}]
    this.outputs = [];           // [{index, outputIndex, node}] (computed)
    this.channels = {};          // animation channels from .chn
    this.userData = {};
    this.spareParmDef = null;    // raw text of .spareparmdef if present
    this.def = null;             // full parsed .def (incl. raw statements)
    this.other = {};             // unrecognised .def statements (e.g. sticky note text/size)
    this.extra = {};             // text of sub-files with unrecognised extensions
  }

  Object.defineProperty(HNode.prototype, 'path', {
    get: function () {
      if (!this.parent) return '/';
      var pp = this.parent.path;
      return (pp === '/' ? '' : pp) + '/' + this.name;
    }
  });

  /** Heuristic: sticky notes / network boxes show up as pseudo-nodes. */
Object.defineProperty(HNode.prototype, 'isSticky', {
  get: function () { return /stick|note/i.test((this.type || '') + ' ' + this.name); }
});

Object.defineProperty(HNode.prototype, 'isNetwork', {
    get: function () { return this.children.length > 0; }
  });

  Object.defineProperty(HNode.prototype, 'depth', {
    get: function () { var d = 0, n = this; while (n.parent) { d++; n = n.parent; } return d; }
  });

  HNode.prototype.child = function (name) { return this._childMap[name] || null; };

  HNode.prototype._addChild = function (name) {
    var c = this._childMap[name];
    if (!c) { c = new HNode(name, this); this._childMap[name] = c; this.children.push(c); }
    return c;
  };

  /** Resolve an absolute ("/obj/geo1") or relative ("../merge1", "sub/x") path. */
  HNode.prototype.find = function (p) {
    var n = this;
    if (p.charAt(0) === '/') { while (n.parent) n = n.parent; }
    var parts = p.split('/');
    for (var i = 0; i < parts.length; i++) {
      var s = parts[i];
      if (!s || s === '.') continue;
      if (s === '..') { n = n.parent; } else { n = n && n.child(s); }
      if (!n) return null;
    }
    return n;
  };

  HNode.prototype.parm = function (name) {
    for (var i = 0; i < this.parms.length; i++) if (this.parms[i].name === name) return this.parms[i];
    return null;
  };

  /** {parmName: value} */
  HNode.prototype.parmValues = function () {
    var o = {};
    this.parms.forEach(function (p) { o[p.name] = p.value; });
    return o;
  };

  /** Raw text of any sub-file by extension, e.g. node.getRaw('def') */
  HNode.prototype.getRaw = function (ext) {
    return this.files[ext] ? utf8.decode(this.files[ext]) : null;
  };

  HNode.prototype.walk = function (cb) {
    if (cb(this) === false) return false;
    for (var i = 0; i < this.children.length; i++) {
      if (this.children[i].walk(cb) === false) return false;
    }
    return true;
  };

  HNode.prototype.toJSON = function (opts) {
    var withParms = !opts || opts.parms !== false;
    var o = { name: this.name, path: this.path, type: this.type };
    if (this.position) o.position = this.position;
    if (this.comment) o.comment = this.comment;
    if (Object.keys(this.flags).length) o.flags = this.flags;
    if (this.inputs.length) {
      o.inputs = this.inputs.map(function (c) {
        return { index: c.index, source: c.node ? c.node.path : c.sourceName, outputIndex: c.outputIndex };
      });
    }
    if (Object.keys(this.other).length) o.other = this.other;
    if (Object.keys(this.extra).length) o.extra = this.extra;
    if (Object.keys(this.channels).length) {
      var anim = {};
      var chs = this.channels;
      Object.keys(chs).forEach(function (k) { anim[k] = { attrs: chs[k].attrs, fps: chs[k].fps, keys: chs[k].keys }; });
      o.animation = anim;
    }
    if (withParms && this.parms.length) o.parms = this.parmValues();
    if (this.children.length) o.children = this.children.map(function (c) { return c.toJSON(opts); });
    return o;
  };

  // ---------------------------------------------------------------------------
  // File model
  // ---------------------------------------------------------------------------

  var KNOWN_EXT = ['init', 'def', 'parm', 'chn', 'userdata', 'spareparmdef'];
  var NODE_NAME_RE = /^[A-Za-z0-9_\-]+$/;

  function HoudiniFile(entries) {
    this.entries = entries;
    this.files = Object.create(null);   // archive path -> Uint8Array (every entry)
    this.root = new HNode('', null);    // virtual "/" node
    this.variables = {};
    this.houdiniVersion = null;
    this._build();
  }

  HoudiniFile.prototype._text = function (name) {
    return this.files[name] ? utf8.decode(this.files[name]) : null;
  };

  HoudiniFile.prototype._build = function () {
    var self = this;

    // 1. Sort entries into nodes
    this.entries.forEach(function (e) {
      if (e.isDir) return;
      self.files[e.name] = e.data;

      var parts = e.name.split('/');
      var base = parts.pop();
      if (!base || base.charAt(0) === '.') return;           // global files like .variables
      var dot = base.lastIndexOf('.');
      if (dot <= 0) return;
      var nodeName = base.slice(0, dot), ext = base.slice(dot + 1);

      var segs = parts.concat([nodeName]);
      if (!segs.every(function (s) { return NODE_NAME_RE.test(s); })) return;  // e.g. HDA defs

      var node = self.root;
      segs.forEach(function (s) { node = node._addChild(s); });
      node.files[ext] = e.data;
    });

    // 2. Parse each node's sub-files
    this.root.walk(function (n) {
      if (n === self.root) return;
      var f = function (ext) { return n.getRaw(ext); };
      var t;

      if ((t = f('init')) !== null) {
        n.init = parseKeyValueLines(t);
        n.type = n.init.type || null;
      }
      if ((t = f('def')) !== null) {
        var d = parseDef(t);
        n.def = d; n.position = d.position; n.flags = d.flags; n.comment = d.comment;
        n.color = d.color; n.stat = d.stat; n.inputs = d.inputs.slice(); n.other = d.other;
      }
      if ((t = f('chn')) !== null) n.channels = parseChannels(t);
      if ((t = f('parm')) !== null) {
        var p = parseParmFile(t);
        n.parms = p.parms; n.parmMeta = p.meta;
        // link parameters to animation channels where possible
        n.parms.forEach(function (parm) {
          var xyz = ['x', 'y', 'z', 'w'];
          parm.channels = parm.values.map(function (v, i) {
            if (v.type === 'word' && n.channels[v.value]) return n.channels[v.value];
            var cands = parm.size === 1 ? [parm.name]
              : [parm.name + xyz[i], parm.name + (i + 1)];
            for (var k = 0; k < cands.length; k++) if (n.channels[cands[k]]) return n.channels[cands[k]];
            return null;
          });
          if (!parm.channels.some(Boolean)) parm.channels = null;
        });
      }
      if ((t = f('userdata')) !== null) n.userData = parseUserData(t);
      if ((t = f('spareparmdef')) !== null) n.spareParmDef = t;
      // keep text of any other sub-file (sticky note content, etc.)
      Object.keys(n.files).forEach(function (ext) {
        if (KNOWN_EXT.indexOf(ext) >= 0) return;
        var bytes = n.files[ext], bin = false;
        for (var i = 0; i < Math.min(bytes.length, 512); i++) if (bytes[i] === 0) { bin = true; break; }
        n.extra[ext] = bin ? '(binary data, ' + bytes.length + ' bytes)' : utf8.decode(bytes);
      });
    });

    // 3. Resolve connections
    this.root.walk(function (n) {
      n.inputs.forEach(function (c) {
        var src = n.parent ? n.parent.find(c.sourceName) : null;
        c.node = src;
        if (src) src.outputs.push({ index: c.index, outputIndex: c.outputIndex, node: n });
      });
    });

    // 4. Globals
    var vars = this._text('.variables');
    if (vars) this.variables = parseVariables(vars);
    this.houdiniVersion = this.variables._HIP_SAVEVERSION || null;
    this.hipName = this.variables.HIPNAME || null;
    this.fps = Number(this.variables.FPS) || 24;
    this.root.walk(function (n) {
      Object.keys(n.channels).forEach(function (k) { annotateChannel(n.channels[k], self.fps); });
    });
  };

  /** Get a node by absolute path, e.g. "/obj/geo1/box1" ("/" returns the virtual root). */
  HoudiniFile.prototype.getNode = function (path) { return this.root.find(path); };

  /** Visit every node (depth-first). Return false from cb to stop. Root is skipped. */
  HoudiniFile.prototype.walk = function (cb) {
    var self = this;
    this.root.walk(function (n) { return n === self.root ? true : cb(n); });
  };

  /** Flat array of all nodes in depth-first order. */
  HoudiniFile.prototype.allNodes = function () {
    var out = [];
    this.walk(function (n) { out.push(n); });
    return out;
  };

  /** Top-level networks (obj, out, shop, mat, stage, ch, img, vex, ...). */
  HoudiniFile.prototype.networks = function () { return this.root.children.slice(); };

  HoudiniFile.prototype.findNodes = function (pred) {
    return this.allNodes().filter(pred);
  };

  HoudiniFile.prototype.nodesByType = function (type) {
    return this.findNodes(function (n) { return n.type === type; });
  };

  /** ASCII outline of the hierarchy. */
  HoudiniFile.prototype.treeString = function () {
    var lines = [];
    (function rec(n, prefix, last, isTop) {
      if (!isTop) lines.push(prefix + (last ? '└─ ' : '├─ ') + n.name + (n.type ? '  [' + n.type + ']' : ''));
      var kids = n.children;
      kids.forEach(function (k, i) {
        rec(k, isTop ? '' : prefix + (last ? '   ' : '│  '), i === kids.length - 1, false);
      });
    })(this.root, '', true, true);
    return lines.join('\n');
  };

  HoudiniFile.prototype.toJSON = function (opts) {
    return {
      houdiniVersion: this.houdiniVersion,
      variables: this.variables,
      networks: this.root.children.map(function (c) { return c.toJSON(opts); })
    };
  };

  // ---------------------------------------------------------------------------
  // Public API
  // ---------------------------------------------------------------------------

  async function fromArrayBuffer(buf) {
    buf = await maybeGunzip(buf);
    return new HoudiniFile(parseCpio(buf));
  }
  async function fromFile(file) { return fromArrayBuffer(await file.arrayBuffer()); }
  async function fromURL(url, init) {
    var res = await fetch(url, init);
    if (!res.ok) throw new Error('HTTP ' + res.status + ' while fetching ' + url);
    return fromArrayBuffer(await res.arrayBuffer());
  }

  global.HoudiniReader = {
    fromArrayBuffer: fromArrayBuffer,
    fromFile: fromFile,
    fromURL: fromURL,
    HoudiniFile: HoudiniFile,
    HNode: HNode,
    // low-level pieces, exposed for advanced use / debugging
    parseCpio: parseCpio,
    parseParmFile: parseParmFile,
    parseDef: parseDef,
    parseChannels: parseChannels,
    annotateChannel: annotateChannel
  };

  if (typeof module === 'object' && module.exports) module.exports = global.HoudiniReader;

})(typeof self !== 'undefined' ? self : this);
