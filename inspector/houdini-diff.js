/*!
 * houdini-diff.js — compare two Houdini scene files read with houdini-reader.js
 *
 * Load AFTER houdini-reader.js. Adds to the global HoudiniReader:
 *
 *     HoudiniReader.diff(fileA, fileB, options)  -> result
 *     HoudiniReader.formatDiff(result, {names})  -> plain-text report
 *     HoudiniReader.makeRenamer(rule)            -> function(string) -> string   (or null)
 *
 * Usage
 * -----
 *     const a = await HoudiniReader.fromFile(fileA);
 *     const b = await HoudiniReader.fromFile(fileB);
 *     const res = HoudiniReader.diff(a, b, {
 *       // optional: rewrite node names before matching, per file
 *       renameB: { search: '_v2', replace: '_v1' },
 *       ignorePosition: true,                      // default true
 *       groups: ['Parameters', 'Inputs']           // optional: only compare these categories
 *     });
 *     console.log(res.summary);                    // {added, removed, changed, unchanged}
 *     console.log(HoudiniReader.formatDiff(res));
 *
 * Rename rule  { search, replace, regex=false, caseSensitive=false, values=true }
 *   - Every node name is rewritten with search -> replace before the two trees are matched.
 *   - Input connections (which hold node names) are always rewritten the same way.
 *   - values=true also rewrites parameter values, expressions, comments and other text, so
 *     references such as ch("../box_v2/size") still line up after the rename.
 *   - regex=true treats `search` as a JavaScript regular expression ($1, $& etc. work in `replace`).
 *
 * Result
 * ------
 *   {
 *     root:     { children:[DiffNode], hasDiff },
 *     summary:  { added, removed, changed, unchanged },   // counted per node
 *     renamed:  { a: n, b: n },                           // how many node names the rule changed
 *     warnings: [string]                                  // e.g. rename collisions
 *   }
 *   DiffNode = { name, path, status: 'same'|'changed'|'added'|'removed',
 *                a: HNode|null, b: HNode|null,            // original nodes (original names kept)
 *                props: [{group, key, a, b}],             // differing properties (undefined = absent)
 *                children: [DiffNode], hasDiff }          // hasDiff: this node or a descendant differs
 *
 * Categories (the `groups` option; omit to compare all of them):
 *   'Node' (type, flags, comment, color, position), 'Inputs', 'Parameters', 'Animation',
 *   'Other .def', 'Other files', 'User data'.   Available as HoudiniReader.diff.GROUPS.
 *   Added/removed nodes are always reported; the category filter only decides which
 *   differences count as a change on nodes that exist in both files.
 *
 * Note: Houdini stores only non-default parameters, so a parameter that is "absent" on one
 * side simply sits at its default there. Timestamps and author info are never compared.
 */
(function (global) {
  'use strict';

  var HR = global.HoudiniReader;
  if (!HR) throw new Error('houdini-diff.js must be loaded after houdini-reader.js');

  var GROUPS = ['Node', 'Inputs', 'Parameters', 'Animation', 'Other .def', 'Other files', 'User data'];

  // ---------------------------------------------------------------------------
  // Rename rule
  // ---------------------------------------------------------------------------

  function escapeRe(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }

  /** Build a string -> string rewriter from a rule. Returns null for an empty rule. Throws on a bad regex. */
  function makeRenamer(rule) {
    if (!rule || !rule.search) return null;
    var re = new RegExp(rule.regex ? rule.search : escapeRe(rule.search), 'g' + (rule.caseSensitive ? '' : 'i'));
    var rep = rule.replace == null ? '' : String(rule.replace);
    if (rule.regex) return function (s) { return s.replace(re, rep); };
    return function (s) { return s.replace(re, function () { return rep; }); };   // literal replacement ($ is not special)
  }

  function identity(s) { return s; }

  // ---------------------------------------------------------------------------
  // Property extraction
  // ---------------------------------------------------------------------------

  function fmt(v) { return Array.isArray(v) ? v.join(' ') : String(v); }
  function round4(x) { return typeof x === 'number' ? +x.toFixed(4) : x; }

  function fmtValue(v) {
    if (v.type === 'string') return JSON.stringify(v.value);
    if (v.type === 'group') return '[' + v.raw.join(' ') + ']';
    return String(v.value);
  }

  function kvStr(o) {
    return Object.keys(o).sort().map(function (k) { return k + '=' + fmt(o[k]); }).join(' ');
  }

  function channelStr(ch) {
    var lines = [], at = kvStr(ch.attrs);
    if (at) lines.push(at);
    ch.segments.forEach(function (s, i) { lines.push('[' + (i + 1) + '] ' + kvStr(s)); });
    return lines.join('\n');
  }

  /** Flatten a node into [{group, key, value:string}] (value text already passed through V). */
  function nodeProps(n, o) {
    var out = [], V = o.V;
    function add(group, key, value) {
      if (o.groups && o.groups.indexOf(group) < 0) return;
      out.push({ group: group, key: key, value: value });
    }

    add('Node', 'type', n.type || '');
    if (n.comment) add('Node', 'comment', V(n.comment));
    if (n.color) add('Node', 'color', n.color.join(' '));
    if (!o.ignorePosition && n.position) add('Node', 'position', n.position.map(round4).join(' '));
    Object.keys(n.flags).forEach(function (k) { add('Node', 'flag ' + k, n.flags[k] ? 'on' : 'off'); });

    n.inputs.slice().sort(function (x, y) { return x.index - y.index; }).forEach(function (c) {
      add('Inputs', 'input ' + c.index, o.N(c.sourceName) + (c.outputIndex ? ' (output ' + c.outputIndex + ')' : ''));
    });
    n.parms.forEach(function (p) { add('Parameters', p.name, V(p.values.map(fmtValue).join('   '))); });
    Object.keys(n.channels).forEach(function (k) { add('Animation', k, V(channelStr(n.channels[k]))); });
    Object.keys(n.other).forEach(function (k) {
      var v = n.other[k];
      add('Other .def', k, V(Array.isArray(v) ? v.join(' ') : [v.args.join(' ')].concat(v.lines).join('\n')));
    });
    Object.keys(n.extra).forEach(function (k) { add('Other files', '.' + k, V(n.extra[k])); });
    if (n.spareParmDef != null) add('Other files', '.spareparmdef', V(n.spareParmDef));
    Object.keys(n.userData).forEach(function (k) { add('User data', k, V(String(n.userData[k]))); });
    return out;
  }

  function diffProps(pa, pb) {
    var ma = new Map(), mb = new Map(), order = [];
    function idx(list, m) {
      list.forEach(function (p) {
        var k = p.group + '\u0000' + p.key;
        if (!m.has(k)) { m.set(k, p); if (order.indexOf(k) < 0) order.push(k); }
      });
    }
    idx(pa, ma); idx(pb, mb);
    var res = [];
    order.forEach(function (k) {
      var x = ma.get(k), y = mb.get(k);
      if (x && y && x.value === y.value) return;
      var p = x || y;
      res.push({ group: p.group, key: p.key, a: x ? x.value : undefined, b: y ? y.value : undefined });
    });
    // stable sort by group order
    return res
      .map(function (p, i) { return { p: p, i: i, g: GROUPS.indexOf(p.group) }; })
      .sort(function (x, y) { return (x.g - y.g) || (x.i - y.i); })
      .map(function (x) { return x.p; });
  }

  // ---------------------------------------------------------------------------
  // Tree diff
  // ---------------------------------------------------------------------------

  function natural(a, b) { return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' }); }

  /** Children of `node` keyed by their (possibly renamed) name. */
  function childMap(node, sideOpts, side, ctx) {
    var m = new Map();
    node.children.forEach(function (c) {
      var nn = sideOpts.N(c.name);
      if (!nn || m.has(nn)) {
        if (nn) ctx.warnings.push('Rename collision in ' + side.toUpperCase() + ': "' + c.name + '" → "' + nn +
          '" already exists under ' + node.path + ' — kept original name.');
        nn = c.name;
        var k = 2; while (m.has(nn)) nn = c.name + '~' + (k++);
      }
      if (nn !== c.name) ctx.renamed[side]++;
      m.set(nn, c);
    });
    return m;
  }

  function diffChildren(a, b, parentPath, ctx) {
    var ca = a ? childMap(a, ctx.oa, 'a', ctx) : new Map();
    var cb = b ? childMap(b, ctx.ob, 'b', ctx) : new Map();
    var names = [];
    ca.forEach(function (_, k) { names.push(k); });
    cb.forEach(function (_, k) { if (!ca.has(k)) names.push(k); });
    names.sort(natural);
    return names.map(function (nm) {
      return diffNode(ca.get(nm) || null, cb.get(nm) || null, nm, parentPath, ctx);
    });
  }

  function diffNode(a, b, name, parentPath, ctx) {
    var d = {
      name: name,
      path: (parentPath === '/' ? '' : parentPath) + '/' + name,
      status: 'same', a: a, b: b, props: [], children: [], hasDiff: false
    };
    if (!a || !b) {
      var n = a || b;
      d.status = a ? 'removed' : 'added';
      d.props = nodeProps(n, a ? ctx.oa : ctx.ob).map(function (p) {
        return { group: p.group, key: p.key, a: a ? p.value : undefined, b: b ? p.value : undefined };
      });
    } else {
      d.props = diffProps(nodeProps(a, ctx.oa), nodeProps(b, ctx.ob));
      d.status = d.props.length ? 'changed' : 'same';
    }
    ctx.stats[d.status === 'same' ? 'unchanged' : d.status]++;
    d.children = diffChildren(a, b, d.path, ctx);
    d.hasDiff = d.status !== 'same' || d.children.some(function (c) { return c.hasDiff; });
    return d;
  }

  function diff(fileA, fileB, options) {
    options = options || {};
    var ra = makeRenamer(options.renameA), rb = makeRenamer(options.renameB);
    var ignorePosition = options.ignorePosition !== false;
    var groups = Array.isArray(options.groups) ? options.groups : null;
    function sideOpts(rule, r) {
      return { N: r || identity, V: (r && rule.values !== false) ? r : identity, ignorePosition: ignorePosition, groups: groups };
    }
    var ctx = {
      oa: sideOpts(options.renameA, ra),
      ob: sideOpts(options.renameB, rb),
      stats: { added: 0, removed: 0, changed: 0, unchanged: 0 },
      renamed: { a: 0, b: 0 },
      warnings: []
    };
    var children = diffChildren(fileA.root, fileB.root, '/', ctx);
    return {
      root: { name: '', path: '/', status: 'same', children: children,
              hasDiff: children.some(function (c) { return c.hasDiff; }) },
      summary: ctx.stats,
      renamed: ctx.renamed,
      warnings: ctx.warnings
    };
  }

  // ---------------------------------------------------------------------------
  // Plain-text report
  // ---------------------------------------------------------------------------

  function countTree(d) { var n = 1; d.children.forEach(function (c) { n += countTree(c); }); return n; }

  function formatDiff(res, opts) {
    opts = opts || {};
    var lines = [];
    if (opts.names) {
      lines.push('A: ' + opts.names[0]);
      lines.push('B: ' + opts.names[1]);
    }
    var s = res.summary;
    lines.push(s.added + ' added, ' + s.removed + ' removed, ' + s.changed + ' changed, ' + s.unchanged + ' unchanged');
    lines.push('');
    function show(v) { return v === undefined ? '(not set)' : v === '' ? '(empty)' : v.replace(/\n/g, '\\n'); }
    (function rec(list) {
      list.forEach(function (d) {
        if (!d.hasDiff) return;
        var mark = { added: '+', removed: '-', changed: '~', same: ' ' }[d.status];
        var node = d.a || d.b;
        var line = mark + ' ' + d.path + (node.type ? '  [' + node.type + ']' : '');
        if (d.status === 'added' || d.status === 'removed') {
          var sub = countTree(d) - 1;
          if (sub) line += '  (+' + sub + ' descendant node' + (sub > 1 ? 's' : '') + ')';
          lines.push(line);
          return;
        }
        lines.push(line);
        if (d.status === 'changed') {
          d.props.forEach(function (p) {
            lines.push('      ' + p.key + ': ' + show(p.a) + '  →  ' + show(p.b));
          });
        }
        rec(d.children);
      });
    })(res.root.children);
    if (!res.root.hasDiff) lines.push('No differences.');
    if (res.warnings.length) { lines.push(''); res.warnings.forEach(function (w) { lines.push('! ' + w); }); }
    return lines.join('\n');
  }

  diff.GROUPS = GROUPS.slice();
  HR.diff = diff;
  HR.formatDiff = formatDiff;
  HR.makeRenamer = makeRenamer;

})(typeof self !== 'undefined' ? self : this);
