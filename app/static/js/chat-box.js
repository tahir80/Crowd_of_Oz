(function(){
  var messageResponses = '';
  var chat = {
    messageToSend: '',
    username: '',
    loggedIn: false,
    socket: null,
    typed: 0,
    stt: 0,

    // $SCRIPT_ROOT:{{ request.script_root|tojson|safe }},
    // messageResponses: '',
    init: function() {
      this.cacheDOM();
      this.subscribe();
      this.bindEvents();
      this.render();

    },
    cacheDOM: function() {
      this.$chatHistory = $('.chat-history');
      this.$button = $('#send');
      this.$textarea = $('#message-to-send');
      this.$chatHistoryList =  this.$chatHistory.find('ul');
      this.$submit_task_btn = $('#submit_task');
      this.$start = $('#start');

    },
    bindEvents: function() {
      this.$button.on('click', this.addMessage.bind(this));
      this.$textarea.on('keyup', this.addMessageEnter.bind(this));
      this.$textarea.on('keypress', this.keyPressed.bind(this));
      this.$submit_task_btn.on('click', this.submitJob.bind(this));
      this.$start.on('click', this.stt.bind(this));

    },

    keyPressed: function(){
      this.typed = 1;
      console.log('key was pressed' + this.typed);
    },

    stt: function(){
      // this.stt = 1;
      // console.log('stt was pressed' + this.stt);
      $("#start").css("background-color", "#ff0000");
      fetch('/api/speech-to-text/token')
        .then(function(response) {
          return response.text();
        }).then(function(token) {
          var stream = WatsonSpeech.SpeechToText.recognizeMicrophone({
            token: token,
            outputElement: '#message-to-send', // CSS selector or DOM Element
            keepMicrophone: true
            // speaker_labels: true,
            // format: false
          });

          stream.on('data', function(data) {
            if (data.results[0] && data.results[0].final) {
              stream.stop();
              // console.log('stop listening.');
              localStorage.setItem("stt", 1);
              $("#start").css("background-color", "#33cc33");
            }
          });

          stream.on('error', function(err) {
            console.log(err);
          });

        }).catch(function(error) {
          console.log(error);
        });
    },

    submitJob: function() {

      var r = confirm("Are you Sure you want to submit?");
      if (r == true) {
        stopTimer();
        this.socket.emit('submit_active', {
          worker: this.gup("workerId"),
          time_waited: result,
          reward: reward,
          aid: this.gup("assignmentId"),
          hit_id: this.gup("hitId")
        });
        this.socket.disconnect();
        // submit to AMT server
        var string = "SUBMIT_WORK_ACTIVE";
        $('input[name="user-input"]').val(string);
        $("#endForm").submit();
        // window.parent.$('#iframe_contents').attr('src', "https://pepperanywhere.herokuapp.com/feedback?workerId=" + this.gup("workerId") +
        //   "&time_waited=" + result + "&reward=" + reward + "&stage=active" +
        //   "&assignmentId=" + this.gup("assignmentId") + "&hitId=" + this.gup("hitId"));
      }
    },

    gup:function(name) {
        name = name.replace(/[\[]/,"\\\[").replace(/[\]]/,"\\\]");
        var regexS = "[\\?&]"+name+"=([^&#]*)";
        var regex = new RegExp(regexS);
        var results = regex.exec(window.location.href);
        if(results == null)
         return "";
        else
         return unescape(results[1]);
    },

    render: function() {
      this.scrollToBottom();

      if (this.messageToSend.trim() !== '') {

        this.sendMessage();

       var dt = new Date().toLocaleTimeString().
               replace(/([\d]+:[\d]{2})(:[\d]{2})(.*)/, "$1$3");

       $(".chat-history ul").append("<li class='clearfix'> <div class='message-data align-right'> "+
       "<span class='message-data-time'>"+dt+", Today</span> "+
       "<span class='message-data-name'>You</span> <i class='fa fa-circle me'></i></div>"+
       "<div class='message other-message float-right'> "+this.messageToSend+"</div></li>");
       this.scrollToBottom();
       this.$textarea.val('');
      }
    },

    addMessage: function() {
      this.messageToSend = this.$textarea.val();
      this.render();
    },

    addMessageEnter: function(event) {

        if (event.keyCode === 13) {
          this.addMessage();
        }
    },
    scrollToBottom: function() {
       // this.$chatHistory.scrollTop(this.$chatHistory[0].scrollHeight);
       $('.chat-history').animate({
                scrollTop: $('.chat-history')[0].scrollHeight}, "slow");
    },
    getCurrentTime: function() {
      return new Date().toLocaleTimeString().
              replace(/([\d]+:[\d]{2})(:[\d]{2})(.*)/, "$1$3");
    },

    // send message
    sendMessage:function() {

      this.stt = Number(localStorage.getItem("stt"));

      console.log(this.stt);
      console.log(this.typed);

      var msgType = '';
      if(this.stt === 1 && this.typed === 1) {msgType = 'mixed';}
      if(this.stt === 1 && this.typed === 0) {msgType = 'stt';}
      if(this.stt === 0 && this.typed === 1) {msgType = 'typed';}

      console.log(msgType);

      var message = this.$textarea.val();
      this.socket.emit('fromcrowd', {message: message, worker: this.gup("workerId"), aid: this.gup("assignmentId"), msgType: msgType});
      this.$textarea.val('');

      localStorage.setItem("stt", 0);
      this.stt = 0;
      this.typed = 0;
      // this.$button.attr("DISABLED", "disabled");
      },
    // Subscribe and start receiving messages
    subscribe:function() {
      var namespace = '/chat';
      this.socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
      console.log(location.protocol + '//' + document.domain + ':' + location.port + namespace);

      //start timer as soon as they reach this page
      startTimer();

      this.socket.on('fromuser', this.receivedMessage1.bind(this));
      this.socket.on('display_crowd_response', this.receivedMessage2.bind(this));
      this.socket.on('update_score', this.updateScore.bind(this));
      this.socket.on('stop', this.stopJob.bind(this));
      // this.socket.on('enable_send_button', this.enableSendButton.bind(this));
      this.socket.on('start_progress_bar', this.startProgressBar.bind(this));
    },

    // enableSendButton: function() {
    //   var isDisabled = this.$button.is(':disabled');
    //   if (isDisabled) {
    //     this.$button.removeAttr('disabled');
    //   } else {}
    //
    // },

    startProgressBar: function() {
     this.progressBar();
    },

    receivedMessage1: function(e) {
      // this.scrollToBottom();
       // this.$chatHistory.scrollTop(this.$chatHistory[0].scrollHeight);
      // $('.chat-history').scrollTop($('.chat-history')[0].scrollHeight);
      $('.chat-history').animate({
               scrollTop: $('.chat-history')[0].scrollHeight}, "slow");

     var dt = new Date().toLocaleTimeString().
             replace(/([\d]+:[\d]{2})(:[\d]{2})(.*)/, "$1$3");

     $(".chat-history ul").append("<li class='clearfix'> <div class='message-data'> "+
     "<span class='message-data-name'><i class='fa fa-circle online'></i> Participant</span> "+
     "<span class='message-data-time'>"+ dt+", Today</span></div> <div class='message my-message'>" +e.message+ " </div> </li>");

   },

   receivedMessage2: function(e) {
    if(e.worker === this.gup("workerId")) {} //do nothing
    else {
     $('.chat-history').animate({
              scrollTop: $('.chat-history')[0].scrollHeight}, "slow");

    var dt = new Date().toLocaleTimeString().
            replace(/([\d]+:[\d]{2})(:[\d]{2})(.*)/, "$1$3");

    $(".chat-history ul").append("<li class='clearfix'> <div class='message-data'> "+
    "<span class='message-data-name'><i class='fa fa-circle online'></i> Crowd</span> "+
    "<span class='message-data-time'>"+ dt+", Today</span></div> <div class='message my-message'>" +e.message+ " </div> </li>");
  }
  },

   updateScore: function(data){
     //check whether this worker is the one who should get notification for score update
     if(data.workerId === this.gup("workerId")) {
       $('#total_msgs').text(data.total_msgs);
       $("#selected_msgs").text(data.selected_msgs);
       $("#total_bonus").text(data.bonus);
     }
   },

   stopJob: function(data) {

     stopTimer();

     // alert("The requester wants to finish this job now." +
     // "You will be paid (fix pay as well as bonuses) based on your contribution in waiting and active state.");
  
     this.socket.emit('submit_active', {
       worker: this.gup("workerId"),
       time_waited: result,
       reward: reward,
       aid: this.gup("assignmentId"),
       hit_id: this.gup("hitId")
     });
     this.socket.disconnect();
     // submit to AMT server
     var string = "SUBMIT_WORK_ACTIVE";
     $('input[name="user-input"]').val(string);
     $("#endForm").submit();

     // window.parent.$('#iframe_contents').attr('src', "https://pepperanywhere.herokuapp.com/feedback?workerId=" + this.gup("workerId") +
     //   "&time_waited=" + result + "&reward=" + reward + "&stage=active" +
     //   "&assignmentId=" + this.gup("assignmentId") + "&hitId=" + this.gup("hitId"));

   },


   progressBar: function() {
     var status = this.enterKeyStatus;
     var elem = document.getElementById("myBar");
     // var send_button = this.$button;
     var width = 1;
     var id = setInterval(frame, 70);
     function frame() {
       elem.style.background = "#4CAF50";
       if (width >= 100) {
         clearInterval(id);
         elem.style.background = "red";
         // send_button.attr("DISABLED", "disabled");
         status = false;
       } else {
         if (width >= 70) {
           elem.style.background = "red";
           width++;
           elem.style.width = width + '%';
         } else {
           width++;
           elem.style.width = width + '%';
         }
       }
     } //end of frame
   }



  };

  chat.init();



})();
