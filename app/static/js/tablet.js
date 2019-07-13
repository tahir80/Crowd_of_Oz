
(function() {

  var tablet = {
    socket: null,

    init: function() {
      this.subscribe();
    },

    subscribe: function() {
      var namespace = '/chat';
      this.socket = io.connect(location.protocol + '//' + document.domain + location.port + namespace);
      // console.log(location.protocol + '//' + document.domain + ':' + location.port + namespace);
      this.socket.on('display_to_tablet', function(e) {

         $('#text').text(e.text);

         if(e.text === "Hello, I am Pepper. I am ready to talk with you. How can I help you?") {
           countdown( "ten-countdown", 10, 0 );
         }

      }.bind(this));


      this.socket.on('workers_status', function(e) {

         $('#active').text(e.active);
         $('#waiting').text(e.waiting);
         $('#tutorial').text(e.tutorial);

      }.bind(this));
    }
  };

  tablet.init();

})();
