var socket;

  var namespace = '/chat';
  socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);
  console.log(location.protocol + '//' + document.domain + ':' + location.port + namespace);


function stop_task() {
    var r = confirm("Are you Sure you want to stop this task?");
    if (r == true) socket.emit('stop_this_job', {});
  }

function expireHIT(taskID) {

    var r = confirm("Are you Sure you want to expire this HIT? " +
                   "Make sure that you have stopped this task before you expire it "+
                    "to avoid exceptions");
                    
    if (r == true) socket.emit('expireHIT', {'taskID': taskID});
     // window.location.href = "https://pepperanywhere.herokuapp.com/list_tasks/"+p_id;
  }
