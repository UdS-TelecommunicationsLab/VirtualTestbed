var http = require("http");

var requestHandler = function(req, res) {
	res.end("Hello World!\n");
};

http.createServer(requestHandler).listen(80);
console.log("Running");
