var OOCSI = (function() {

	var wsUri = "ws://oocsi.id.tue.nl/ws";
	var username;
	var handlers = {};
	var responders = {};
	var calls = {};
	var websocket;
	var connected = false;
	var logger = internalLog;

	function init() {
		logger("CONNECTING to "  + wsUri);
		websocket = new WebSocket(wsUri);
		websocket.onopen = function(evt) {
			onOpen(evt)
		};
		websocket.onclose = function(evt) {
			onClose(evt)
		};
		websocket.onmessage = function(evt) {
			onMessage(evt)
		};
		websocket.onerror = function(evt) {
			onError(evt)
		};
	}

	function onOpen(evt) {
		if(websocket.readyState == WebSocket.OPEN) {
			submit(username);
			connected = true;
		}
		logger("CONNECTED");
	}

	function onClose(evt) {
		logger("DISCONNECTED");
		connected = false;
	}

	function onMessage(evt) {
		websocket.send(".");
		if(evt.data != 'ping') {
			try {
				var e = JSON.parse(evt.data);
				if(e.data.hasOwnProperty('_MESSAGE_ID') && calls.hasOwnProperty(e.data['_MESSAGE_ID'])) {
					var c = calls[e.data['_MESSAGE_ID']];

					if((+new Date) < c.expiration) {
						delete e.data['_MESSAGE_ID'];
						c.fn(e.data);
					}

					delete calls[e.data['_MESSAGE_ID']];
				} else if(handlers[e.recipient] !== undefined) {
					handlers[e.recipient](e);
				} else {
					logger('no handler for event: ' + evt.data);
				}
			} catch(e) {
				logger('ERROR: parse exception for event data ' + evt.data);
			}
			logger('RESPONSE: ' + evt.data);
		}
	}

	function onError(evt) {
		logger('ERROR: ' + evt.data);
	}

	function waitForSocket(fn) {
		if(!websocket || websocket.readyState == WebSocket.CONNECTING) {
			setTimeout(function() { waitForSocket(fn) }, 200);
		} else {
			fn();
		}
	}

	function internalClose() {
		websocket && websocket.close();
	}

	function submit(message) {
		if(websocket && websocket.send(message)) {
			logger("SENT: " + message);
		}
	}

	function internalLog(message) {
		// do nothing by default
	}

	function internalSend(client, data) {
		connected && submit('sendjson ' + client + ' '+ JSON.stringify(data));
	}

	function internalCall(call, data, timeout, fn) {
		if(connected) {
			var uuid = guid();
			calls[uuid] = {expiration: (+new Date) + timeout, fn: fn};
			data['_MESSAGE_ID'] = uuid;
			data['_MESSAGE_HANDLE'] = call;
			submit('sendjson ' + call + ' '+ JSON.stringify(data));
		}
	}

	function internalRegister(call, fn) {
		if(connected) {
			responders[call] = {fn: fn};
			internalSubscribe(call, function(e) {
				var response = {'_MESSAGE_ID': e.data['_MESSAGE_ID']};
				fn(e.data, response);
				internalSend(e.sender, response);
			});
		}
	}

	function internalSubscribe(channel, fn) {
		if(connected) {
			submit('subscribe ' + channel);
			handlers[channel] = fn;
		}
	}

	function internalUnsubscribe(channel) {
		if(connected) {
			submit('unsubscribe ' + channel);
			handlers[channel] = function() {};
		}
	}

	function guid() {
		function s4() {
			return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
		}
  		return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
	}

	return {
		connect: function(server, clientName, fn) {
			wsUri = server;
			username = clientName && clientName.length > 0 ? clientName : "webclient_" + +(new Date());
			handlers[clientName] = fn;
			init();
		},
		send: function(recipient, data) {
			waitForSocket(function() {
				internalSend(recipient, data);
			});
		},
		call: function(call, data, timeout, fn) {
			waitForSocket(function() {
				internalCall(call, data, timeout, fn);
			});
		},
		register: function(call, fn) {
			waitForSocket(function() {
				internalRegister(call, fn);
			});
		},
		subscribe: function(channel, fn) {
			waitForSocket(function() {
				internalSubscribe(channel, fn);
			});
		},
		unsubscribe: function(channel) {
			waitForSocket(function() {
				internalUnsubscribe(channel);
			});
		},
		isConnected: function() {
			return connected;
		},
		close: function() {
			waitForSocket(function() {
				internalClose();
			});
		},
		handlers: function() {
			return handlers;
		},
		logger: function(fn) {
			logger = fn;
		}
	};

})();
