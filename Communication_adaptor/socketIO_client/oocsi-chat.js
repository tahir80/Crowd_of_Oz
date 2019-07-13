var loggedIn = false;
var username = '';
var $ = jQuery;
// catch submissions by pressing Enter
$('#input').keypress(function(event) {
    if(event.which == 13) {
      // event.preventDefault();
      if(loggedIn) {
      // if logged in, send as message
        sendMessage();
      } else {
        // if not yet logged in, do a login
        login();
      }
    }
  });
  // focus on input field
$('#input')[0].focus();
// catch submissions by clicking the button
$('#submit').click(function(event) {
    // event.preventDefault();
  if(loggedIn) {
    // if logged in, send as message
    sendMessage();
    $('#input')[0].focus();
  } else {
      // if not yet logged in, do a login
    login();
    $('#input')[0].focus();
  }
  });
// send message
function sendMessage() {
  // get message and check for length
  var message = $('#input').val();
  if(message.length > 0) {
    // print message on screen
    var b = $('<p></p>').addClass('me').text('>> ' + message);
    $('#output').append(b);
    b[0].scrollIntoView();
    // reset message input field
    $('#input').val('');
    // send message to oocsi
    OOCSI.send("myChannel", {message: message});
  }
}
// login and start oocsi
function login() {
    // connect to OOCSI server running on IP and port 9000
  if($('#input').val().length > 0) {
    username = $('#input').val();
    OOCSI.connect("ws://oocsi.id.tue.nl/ws", username);
  } else {
    OOCSI.connect("ws://oocsi.id.tue.nl/ws");
  }
    // subscribe to the channel "colorChange"
    OOCSI.subscribe("myChannel", receivedMessages);
    // optional logging to console
    // OOCSI.logger(function(msg) {console.log(msg)});
    // announce me in channel
    OOCSI.send("myChannel", {message: "Hi, I just joined the chat!"});
    setTimeout(function() {
      if(OOCSI.isConnected()) {
      loggedIn = true;
        // print log in success
      var b = $('<p></p>').addClass('me').text('>> logged in as ' + username);
      $('#output').append(b);
      $('#output').show();
      // reset input field
      $('#input').val('');
      // relabel login/send button
        $('#submit').text('send');
      }
    }, 200);
    // test
    setTimeout(function() {
      OOCSI.call('addition.addnineteen2', {value: 2}, 5000, function(data) {
        console.log(data)
      });
    }, 2000);
}

function receivedMessages(e) {
  var b = $('<p></p>').addClass('others').text(e.sender + ': ' + e.data.message);
  $('#output').append(b);
  b[0].scrollIntoView();
}
