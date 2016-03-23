$(document).ready(function(){ 
  if ("WebSocket" in window) {
    var domain = window.location.host
    var ws = new WebSocket("ws://"+domain+"/datasync");
    
    ws.onopen = function() {
      console.log('Mocha Dick DataSync online');
    };
    
    ws.onmessage = function (evt) {
      
      // WebSocket DataSync to UI
      var json = evt.data;
      msg = JSON.parse(json);
      if (msg['draft_points'] != null) {
        $('#draftPoints').html(msg['draft_points']);
      }
      // if (msg['ui_element'] != null) {
      //   $('#ui_element').html(msg['ui_element']);
      // }
    };
    
    ws.onclose = function() {
      console.log('Mocha Dick DataSync offline');
    };
  } else {
    alert("WebSocket not supported");
  }
});