import React, { useState, useRef, useEffect } from "react";
import {
  Container,
  Button,
  Row,
  Col,
} from "reactstrap";
import avatar2 from "../../assets/images/users/mcdonald.jpg";

const Chat = () => {
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hello! How can I help you?",
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  const messagesEndRef = useRef(null);
  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleClick = () => {
    if (!inputMessage.trim()) return;

    const timeNow = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const userMessage = {
      role: "user",
      content: inputMessage,
      time: timeNow,
    };

    const updatedMessages = [...messages, userMessage];

    setInputMessage("");
    setMessages(updatedMessages);

    const messagesForAPI = updatedMessages.map(m => ({
      role: m.role,
      content: m.content
    }));

    console.log(messagesForAPI);

    fetch(`${API_BASE_URL}/non_rag_query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ messages: messagesForAPI }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("API response:", data.answer);

        const botMessage = {
          role: "assistant",
          content: data.answer || "No response",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages(prev => [...prev, botMessage]);
      })
      .catch((error) => {
        console.error("API error:", error);
        const errorMessage = {
          role: "assistant",
          content: "Sorry, there was an error. Please try again later.",
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages(prev => [...prev, errorMessage]);
      });
  };

  return (
    <div className="page-content">
      <Container fluid>
        <div className="chat-wrapper d-lg-flex gap-1 mx-n4 mt-n4 p-1">
          <div className="user-chat w-100 overflow-hidden">
            <div className="chat-content d-lg-flex">
              <div className="w-100 overflow-hidden position-relative">
                <div className="p-3 user-chat-topbar">
                  <Row className="align-items-center">
                    <Col sm={4} xs={8}>
                      <div className="d-flex align-items-center">
                        <div className="flex-grow-1 overflow-hidden">
                          <h5 className="text-truncate mb-0 fs-16">
                            McDonald`s Chatbot
                          </h5>
                          <p className="text-truncate text-muted fs-14 mb-0">
                            <small>Online</small>
                          </p>
                        </div>
                      </div>
                    </Col>
                  </Row>
                </div>

                <div className="chat-conversation p-3 p-lg-4" style={{ maxHeight: "400px", overflowY: "auto" }}>
                  <ul className="list-unstyled chat-conversation-list">
                    {messages.map((msg, idx) => (
                      <li
                        key={idx}
                        className={`chat-list ${msg.role === "assistant" ? "left" : "right"}`}
                      >
                        <div className="conversation-list">
                          {msg.role === "assistant" && (
                            <div className="chat-avatar">
                              <img src={avatar2} alt="" />
                            </div>
                          )}
                          <div className="user-chat-content">
                            <div className="ctext-wrap">
                              <div className="ctext-wrap-content">
                                <p className="mb-0 ctext-content">{msg.content}</p>
                              </div>
                            </div>
                            <div className="conversation-name">
                              <small className="text-muted time">{msg.time}</small>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                  <div ref={messagesEndRef} />
                </div>

                <div className="chat-input-section p-3 p-lg-4">
                  <Row className="g-0 align-items-center">
                    <div className="col">
                      <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        className="form-control chat-input bg-light border-light"
                        placeholder="Type your message..."
                      />
                    </div>
                    <div className="col-auto">
                      <Button
                        color="success"
                        className="chat-send"
                        onClick={handleClick}
                      >
                        <i className="ri-send-plane-2-fill align-bottom"></i>
                      </Button>
                    </div>
                  </Row>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </div>
  );
};

export default Chat;
