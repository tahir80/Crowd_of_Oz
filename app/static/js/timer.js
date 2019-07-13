var timer = 0;
var reward = 0;
var result = 0;

var temp_timer = '';
var temp_reward = '';

var sec = 0;
var seconds;

function startTimer() {
  seconds = sec;
  timer = setInterval(function() {
    seconds++;
    document.getElementById("timer").innerText = SecondsTohhmmss(seconds);
    document.getElementById("reward").innerText = real_time_reward(seconds);
    // document.getElementById("minutes").innerText = parseInt(seconds / 60);
  }, 1000);
}

function callback() {
  clearInterval(timer);
}
function stopTimer() {
  sec = seconds;
  document.getElementById("timer").innerText = result;
  document.getElementById("reward").innerText = reward;
  callback();
}
function real_time_reward(seconds) {
  var hourly_rate = 7.25;
  var per_minute_rate = hourly_rate / 60;
  var per_seconds_rate = per_minute_rate / 60;

  reward = per_seconds_rate * seconds;

  reward = Math.round(reward * 100) / 100;

  return reward; // round to two decimal places
}

function SecondsTohhmmss(totalSeconds) {
  var hours = Math.floor(totalSeconds / 3600);
  var minutes = Math.floor((totalSeconds - (hours * 3600)) / 60);
  var seconds = totalSeconds - (hours * 3600) - (minutes * 60);

  // round seconds
  seconds = Math.round(seconds * 100) / 100

  result = (hours < 10 ? "0" + hours : hours);
  result += "-" + (minutes < 10 ? "0" + minutes : minutes);
  result += "-" + (seconds < 10 ? "0" + seconds : seconds);
  return result;
}
