
document.getElementById('copy').setAttribute('href','#');
// get_changelogs();


if (!in_houdini()) {
    window.addEventListener('load', videoScroll);
    window.addEventListener('scroll', videoScroll);
}


window.onload = function() {
    if (!qt || !qt.webChannelTransport) {
        // The web channel transport does not exist so we must not
        // be running in the embedded browser.
        return;
    }
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.Python = channel.objects.Python;

        window.Python.runStringExpression(
            "__import__('hou').homeHoudiniDirectory()",
            function(result) {
                document.body.innerHTML = document.body.innerHTML.replace('$HOME/houdini', result);
            }
        );
        
        removeById('manual');
        document.getElementById('copy').innerHTML = 'Automatically Install in the folder:\n "$HOME/houdini"';
        let ps = document.querySelectorAll('section');
        ps.forEach(p => {
            p.setAttribute('style', 'display:none');
        })
    });
}

function in_houdini() {
    return (typeof window.Python != "undefined");
}


function videoScroll() {   
    if (document.querySelectorAll('video[autoplay]').length > 0) {
        var windowHeight = window.innerHeight,
        videoEl = document.querySelectorAll('video[autoplay]');

        for (var i = 0; i < videoEl.length; i++) {
            var thisVideoEl = videoEl[i],
            videoHeight = thisVideoEl.clientHeight,
            videoClientRect = thisVideoEl.getBoundingClientRect().top;

            if ( videoClientRect <= ( (windowHeight) - (videoHeight*.5) ) && videoClientRect >= ( 0 - ( videoHeight*.5 ) ) ) {
                thisVideoEl.play();
            } 
            else {
                thisVideoEl.pause();
            }
        }
    }
}


function get_install_script(url) {
    var styleElem = document.head.appendChild(document.createElement("style"));  // Do it this way because using classList doesn't update the DOM in Houdini
    styleElem.innerHTML = ".glow-on-hover:after {background-color: rgba(0, 128, 0, 0.85) !important;} .bi-clipboard::before {content: \"\\f272\" !important;}";
    if (in_houdini()) {
        // download file and execute it in python
        window.Python.runStatements('import os;import urllib.request;import tempfile;filename = os.path.basename("' + url + '");tmp_path = os.path.join(tempfile.gettempdir(), filename);exec(open(tmp_path).read());');
    
    }
    else {
        // copy to clipboard
        fetch(url).then(function(response) {
            response.text().then(function(text) {
                navigator.clipboard.writeText(text);
            });
        });  
    }
 }


 function get_changelogs() {
    var changelogs = document.getElementById('changelogs');
    var template =  `                    <div class="col-lg-4">
                        <h5>%VERSION%</h5>
                        <p class="font-weight-light mb-0">%CHANGELOG%</p>
                    </div>`;
    changelogs.innerHTML += template;
 }


function removeById(_id) { 
    var e=document.getElementById(_id);
    if(e!==null) e.remove();
}
