var https = require("https");
var fs = require("fs");

var requestHandler = function(req, res) {
	res.end("Hello World!\n");
};

https.createServer({
            key: fs.readFileSync('./cert/key.pem'),
            cert: fs.readFileSync('./cert/cert.pem'),
            rejectUnauthorized: false
}, requestHandler).listen(80);
console.log("Running");
