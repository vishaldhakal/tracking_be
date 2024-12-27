class ChatWidget {
  constructor(config) {
    this.TRACKING_URL = config.TRACKING_URL;
    this.CHAT_URL = config.CHAT_URL;
    this.SITE_ID = config.SITE_ID;
    this.visitorId = localStorage.getItem("visitorId");
    this.visitorEmail = localStorage.getItem("visitorEmail");
    this.activeChat = null;
    this.pollInterval = null;
    this.messages = new Map();
    this.lastMessageTime = 0;

    console.log("ChatWidget initialized with config:", config);
    this.injectStyles();
    this.createWidget();
    this.initializeChat();
  }

  injectStyles() {
    const styles = document.createElement("style");
    styles.textContent = `
            .chat-widget {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
                font-family: system-ui, -apple-system, sans-serif;
            }
            .chat-toggle {
                width: 60px;
                height: 60px;
                border-radius: 30px;
                background: #0070f3;
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
            }
            .chat-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: #ff4444;
                color: white;
                border-radius: 10px;
                padding: 2px 6px;
                font-size: 12px;
                display: none;
            }
            .chat-box {
                position: absolute;
                bottom: 80px;
                right: 0;
                width: 300px;
                height: 400px;
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                display: none;
                flex-direction: column;
            }
            .chat-header {
                padding: 16px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .chat-title {
                font-weight: 600;
                margin: 0;
            }
            .chat-close {
                background: none;
                border: none;
                cursor: pointer;
                color: #666;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            .chat-message {
                max-width: 80%;
                padding: 8px 12px;
                border-radius: 12px;
                margin: 4px 0;
            }
            .chat-message.visitor {
                background: #0070f3;
                color: white;
                align-self: flex-end;
            }
            .chat-message.admin {
                background: #f0f0f0;
                color: black;
                align-self: flex-start;
            }
            .chat-input-container {
                padding: 16px;
                border-top: 1px solid #eee;
                display: flex;
                gap: 8px;
            }
            .chat-input {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 20px;
                outline: none;
            }
            .chat-send {
                background: #0070f3;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                cursor: pointer;
            }
        `;
    document.head.appendChild(styles);
  }

  createWidget() {
    const widget = document.createElement("div");
    widget.className = "chat-widget";
    widget.innerHTML = `
            <button class="chat-toggle">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <span class="chat-badge">0</span>
            </button>
            <div class="chat-box">
                <div class="chat-header">
                    <h3 class="chat-title">Chat with us</h3>
                    <button class="chat-close">✕</button>
                </div>
                <div class="chat-messages"></div>
                <div class="chat-input-container">
                    <input type="text" class="chat-input" placeholder="Type a message...">
                    <button class="chat-send">Send</button>
                </div>
            </div>
        `;
    document.body.appendChild(widget);
    this.bindEvents(widget);
  }

  bindEvents(widget) {
    const toggle = widget.querySelector(".chat-toggle");
    const chatBox = widget.querySelector(".chat-box");
    const closeBtn = widget.querySelector(".chat-close");
    const input = widget.querySelector(".chat-input");
    const sendBtn = widget.querySelector(".chat-send");
    const badge = widget.querySelector(".chat-badge");

    toggle.addEventListener("click", () => {
      chatBox.style.display =
        chatBox.style.display === "none" ? "flex" : "none";
      if (chatBox.style.display === "flex") {
        badge.style.display = "none";
        badge.textContent = "0";
        input.focus();
        this.startPolling();
      } else {
        if (this.pollInterval) {
          clearInterval(this.pollInterval);
        }
      }
    });

    closeBtn.addEventListener("click", () => {
      chatBox.style.display = "none";
    });

    const sendMessage = () => {
      const message = input.value.trim();
      if (!message) return;

      const sendMessageRequest = this.activeChat
        ? this.sendMessage(message)
        : this.startChat(message);

      sendMessageRequest.then(() => {
        input.value = "";
        input.focus();
      });
    };

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keypress", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  appendMessage(message) {
    const messagesContainer = document.querySelector(".chat-messages");
    if (!messagesContainer) return;

    const messageEl = document.createElement("div");
    messageEl.className = `chat-message ${
      message.is_admin ? "admin" : "visitor"
    }`;
    messageEl.innerHTML = `
            ${message.message}
            <div style="font-size: 0.8em; opacity: 0.7;">
                ${new Date(message.created_at).toLocaleTimeString()}
            </div>
        `;
    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  async initializeChat() {
    if (!this.visitorId) return;

    try {
      console.log("Initializing chat for visitor:", this.visitorId);
      const response = await fetch(
        `${this.CHAT_URL}visitor/${encodeURIComponent(this.visitorId)}/chat/`,
        {
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Chat initialization response:", data);

      if (data && data.id) {
        this.activeChat = data;
        if (data.messages?.length) {
          const messagesContainer = document.querySelector(".chat-messages");
          messagesContainer.innerHTML = "";
          data.messages.forEach((message) => {
            this.messages.set(message.id, message);
            this.appendMessage(message);
            if (message.created_at > this.lastMessageTime) {
              this.lastMessageTime = message.created_at;
            }
          });
        }
        this.startPolling();
      }
    } catch (error) {
      console.error("Error initializing chat:", error);
    }
  }

  startPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }

    this.pollInterval = setInterval(() => this.pollMessages(), 1000);
  }

  async pollMessages() {
    if (!this.activeChat) return;

    try {
      const response = await fetch(
        `${this.CHAT_URL}${this.activeChat.id}/messages/?since=${
          this.lastMessageTime || 0
        }`,
        {
          headers: {
            Accept: "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const newMessages = await response.json();
      if (newMessages && newMessages.length > 0) {
        let hasNewAdminMessages = false;

        newMessages.forEach((message) => {
          if (!this.messages.has(message.id)) {
            this.messages.set(message.id, message);
            this.appendMessage(message);
            if (message.created_at > this.lastMessageTime) {
              this.lastMessageTime = message.created_at;
            }
            if (message.is_admin) {
              hasNewAdminMessages = true;
            }
          }
        });

        const chatBox = document.querySelector(".chat-box");
        const badge = document.querySelector(".chat-badge");
        if (chatBox.style.display === "none" && hasNewAdminMessages) {
          const currentCount = parseInt(badge.textContent || "0");
          badge.textContent = currentCount + 1;
          badge.style.display = "block";
        }
      }
    } catch (error) {
      console.error("Error polling messages:", error);
    }
  }

  async sendMessage(message) {
    if (!this.activeChat) {
      try {
        const response = await this.startChat(message);
        return response;
      } catch (error) {
        console.error("Error starting chat:", error);
        throw error;
      }
    }

    try {
      const response = await fetch(`${this.CHAT_URL}message/`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          chat_id: this.activeChat.id,
          message: message,
          is_admin: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const newMessage = await response.json();
      this.messages.set(newMessage.id, newMessage);
      this.appendMessage(newMessage);
      if (newMessage.created_at > this.lastMessageTime) {
        this.lastMessageTime = newMessage.created_at;
      }
      return newMessage;
    } catch (error) {
      console.error("Error sending message:", error);
      throw error;
    }
  }

  async startChat(message) {
    try {
      const response = await fetch(`${this.CHAT_URL}start/`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          visitor_id: this.visitorId,
          website_id: this.SITE_ID,
          message: message,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.activeChat = data;
      this.startPolling();
      return data;
    } catch (error) {
      console.error("Error starting chat:", error);
      throw error;
    }
  }
}

// Export for use in other scripts
window.ChatWidget = ChatWidget;
