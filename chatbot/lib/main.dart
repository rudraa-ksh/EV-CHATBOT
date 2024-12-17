import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(ChatbotApp());
}

class ChatbotApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: ChatbotScreen(),
    );
  }
}

class ChatbotScreen extends StatefulWidget {
  @override
  _ChatbotScreenState createState() => _ChatbotScreenState();
}

class _ChatbotScreenState extends State<ChatbotScreen> {
  final List<Map<String, String>> messages = [];
  final TextEditingController _controller = TextEditingController();
  final String apiUrl = "http://<server IP>/troubleshoot";

  String? sessionCookie; // Cookie variable to store the session dynamically

  // Function to send message to the backend and handle cookie/session
  Future<void> sendMessage(String message) async {
    setState(() {
      messages.add({"sender": "user", "text": message});
    });

    try {
      // Send request with or without an existing session cookie
      var response = await http.post(
        Uri.parse(apiUrl),
        headers: {
          "Content-Type": "application/json",
          if (sessionCookie != null) "Cookie": sessionCookie!,
        },
        body: json.encode({"issue": message.trim()}),
      );

      if (response.statusCode == 200) {
        var data = json.decode(response.body);

        // Capture the `Set-Cookie` header if it's sent by the backend
        var cookies = response.headers['set-cookie'];
        if (cookies != null) {
          sessionCookie = cookies; // Store the session cookie for future requests
        }

        // Handle bot response
        setState(() {
          messages.add({"sender": "bot", "text": data["response"]});
        });

        // Handle the next question if applicable
        if (data.containsKey("next_question")) {
          setState(() {
            messages.add({"sender": "bot", "text": data["next_question"]});
          });
        }
      } else {
        setState(() {
          messages.add({"sender": "bot", "text": "Error: ${response.statusCode}"});
        });
      }
    } catch (e) {
      setState(() {
        messages.add({"sender": "bot", "text": "Failed to connect to server."});
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Troubleshooting Chatbot"),
        backgroundColor: Colors.blueAccent,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final message = messages[index];
                final isUser = message["sender"] == "user";
                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: EdgeInsets.symmetric(vertical: 5, horizontal: 10),
                    padding: EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.blueAccent : Colors.grey[300],
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      message["text"] ?? "",
                      style: TextStyle(color: isUser ? Colors.white : Colors.black),
                    ),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: "Type your message...",
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                  ),
                ),
                IconButton(
                  icon: Icon(Icons.send),
                  color: Colors.blueAccent,
                  onPressed: () {
                    if (_controller.text.isNotEmpty) {
                      sendMessage(_controller.text);
                      _controller.clear();
                    }
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}