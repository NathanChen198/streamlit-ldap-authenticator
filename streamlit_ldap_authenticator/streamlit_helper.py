# Author    : Nathan Chen
# Date      : 08-Feb-2024


from streamlit.components.v1 import html

def _inject_page_script(page_name, action_script, timeout_secs=3):
    page_script = """
        <script type="text/javascript">
            function attempt_exec_page_action(page_name, start_time, timeout_secs, action_fn) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        action_fn(links[i]);
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_exec_page_action, 100, page_name, start_time, timeout_secs, action_fn);
                } else {
                    alert("Unable to locate link to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_exec_page_action("%s", new Date(), %d, function(link) {
                    %s
                });
            });
        </script>
    """ % (page_name, timeout_secs, action_script)
    html(page_script, height=0)

def enablePage(page_name, **kwargs):
    _inject_page_script(page_name, 'link.style.pointerEvents = ""; '
                                   'link.style.opacity = "";', **kwargs)

def hidePage(page_name, **kwargs):
    _inject_page_script(page_name, 'link.style.display = "none";', **kwargs)

def showPage(page_name, **kwargs):
    _inject_page_script(page_name, 'link.style.display = "";', **kwargs)

def disablePage(page_name, **kwargs):
    _inject_page_script(page_name, 'link.style.pointerEvents = "none"; '
                                   'link.style.opacity = 0.5;', **kwargs)
