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
    this.startPolling();
    this.initializeNotifications();
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
                width: 50px;
                height: 50px;
                border-radius: 30px;
                background: black;
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
                background: black;
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
                max-height: 400px;
                min-height: 250px;
                height: auto;
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
                padding: 5px;
                display: flex;
                flex-direction: column;
                gap: 8px;
                scroll-behavior: smooth;
            }
            .chat-message {
                max-width: 80%;
                padding: 8px 11px;
                border-radius: 12px;
                margin: 4px 0;
                font-size: 13px;
                line-height: 1.4;
                word-wrap: break-word;
            }
            .chat-message.visitor {
                background: black;
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
                background: black;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 8px 16px;
                cursor: pointer;
            }
            .chat-message.expanded {
                white-space: normal;
                overflow: visible;
            }
            .chat-message .timestamp {
                font-size: 11px;
                opacity: 0.7;
                margin-top: 8px;
            }
            .chat-message.new-message {
                animation: popIn 0.3s ease-out;
            }
            @keyframes popIn {
                0% { transform: scale(0.8); opacity: 0; }
                100% { transform: scale(1); opacity: 1; }
            }
            .chat-toggle.has-new {
                animation: bounce 1s infinite;
            }
            @keyframes bounce {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }
            .chat-preview {
                position: absolute;
                bottom: 70px;
                right: 60px;
                background: white;
                padding: 8px 12px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.15);
                max-width: 200px;
                font-size: 13px;
                display: none;
                animation: slideIn 0.3s ease-out;
                z-index: 999;
            }
            .chat-preview-content {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                margin-bottom: 4px;
            }
            .chat-preview-time {
                font-size: 11px;
                opacity: 0.7;
            }
            @keyframes slideIn {
                0% { transform: translateY(20px); opacity: 0; }
                100% { transform: translateY(0); opacity: 1; }
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
                    <h4 class="chat-title">Homebaba Team</h4>
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
    const messagesContainer = widget.querySelector(".chat-messages");

    toggle.addEventListener("click", () => {
      const preview = document.querySelector(".chat-preview");
      if (preview) {
        preview.style.display = "none";
      }

      const isOpening = chatBox.style.display === "none";
      chatBox.style.display = isOpening ? "flex" : "none";

      if (isOpening) {
        // Clear and display all stored messages when opening
        messagesContainer.innerHTML = "";
        Array.from(this.messages.values())
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
          .forEach((message) => this.appendMessage(message));

        badge.style.display = "none";
        badge.textContent = "0";
        toggle.classList.remove("has-new");
        input.focus();

        // Scroll to latest message
        setTimeout(() => {
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
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

  appendMessage(message, isNew = false) {
    const messagesContainer = document.querySelector(".chat-messages");
    if (!messagesContainer) return;

    const messageEl = document.createElement("div");
    messageEl.className = `chat-message ${
      message.is_admin ? "admin" : "visitor"
    } ${isNew ? "new-message" : ""}`;

    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const messageText = message.message.replace(urlRegex, (url) => {
      return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
    });

    messageEl.innerHTML = `
        <span class="message-text">${messageText}</span>
        <div class="timestamp">
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
          // Store messages but don't display them yet
          data.messages.forEach((message) => {
            this.messages.set(message.id, message);
            if (message.created_at > this.lastMessageTime) {
              this.lastMessageTime = message.created_at;
            }
          });
        }
      }
    } catch (error) {
      console.error("Error initializing chat:", error);
    }
  }

  startPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }

    const poll = async () => {
      try {
        await this.pollMessages();
      } catch (error) {
        console.error("Error in polling:", error);
      }
    };

    // Initial poll
    poll();
    // Then start interval
    this.pollInterval = setInterval(poll, 1000);
  }

  async pollMessages() {
    if (!this.visitorId) return;

    try {
      // First check for any new chats if we don't have an active chat
      if (!this.activeChat) {
        const chatResponse = await fetch(
          `${this.CHAT_URL}visitor/${encodeURIComponent(this.visitorId)}/chat/`,
          {
            headers: {
              Accept: "application/json",
            },
          }
        );

        if (chatResponse.ok) {
          const chatData = await chatResponse.json();
          if (chatData && chatData.id) {
            this.activeChat = chatData;
            // Process initial messages
            if (chatData.messages?.length) {
              let hasNewAdminMessages = false;
              let latestAdminMessage = null;

              chatData.messages.forEach((message) => {
                if (!this.messages.has(message.id)) {
                  this.messages.set(message.id, message);
                  if (message.created_at > this.lastMessageTime) {
                    this.lastMessageTime = message.created_at;
                  }
                  if (message.is_admin) {
                    hasNewAdminMessages = true;
                    latestAdminMessage = message;
                  }
                }
              });

              // Show notification for new chat
              if (hasNewAdminMessages) {
                const chatToggle = document.querySelector(".chat-toggle");
                const badge = document.querySelector(".chat-badge");

                badge.textContent = "1";
                badge.style.display = "block";
                chatToggle.classList.add("has-new");

                // Show preview message
                const existingPreview = document.querySelector(".chat-preview");
                if (existingPreview) {
                  existingPreview.remove();
                }
                const preview = this.createPreviewMessage(latestAdminMessage);
                preview.style.display = "block";

                if (
                  "Notification" in window &&
                  Notification.permission === "granted"
                ) {
                  new Notification("New message from Homebaba Agent", {
                    body: latestAdminMessage.message,
                  });
                }
              }
            }
          }
        }
      }

      // Skip regular polling if still no active chat
      if (!this.activeChat) return;

      // Regular polling for new messages
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
        let latestAdminMessage = null;

        // Process new messages
        const actualNewMessages = newMessages.filter(
          (message) => !this.messages.has(message.id)
        );

        actualNewMessages.forEach((message) => {
          this.messages.set(message.id, message);
          if (message.created_at > this.lastMessageTime) {
            this.lastMessageTime = message.created_at;
          }
          if (message.is_admin) {
            hasNewAdminMessages = true;
            latestAdminMessage = message;
          }
        });

        const chatBox = document.querySelector(".chat-box");
        const chatToggle = document.querySelector(".chat-toggle");
        const badge = document.querySelector(".chat-badge");

        // Only append actual new messages if chat box is open
        if (chatBox.style.display === "flex" && actualNewMessages.length > 0) {
          actualNewMessages.forEach((message) =>
            this.appendMessage(message, true)
          );
        }

        // Show notifications for new admin messages
        if (hasNewAdminMessages) {
          const currentCount = parseInt(badge.textContent || "0");
          badge.textContent = currentCount + 1;
          badge.style.display = "block";
          chatToggle.classList.add("has-new");

          // Show preview message
          const existingPreview = document.querySelector(".chat-preview");
          if (existingPreview) {
            existingPreview.remove();
          }
          const preview = this.createPreviewMessage(latestAdminMessage);
          preview.style.display = "block";

          if (
            "Notification" in window &&
            Notification.permission === "granted"
          ) {
            new Notification("New message from Homebaba Agent", {
              body: latestAdminMessage.message,
            });
          }
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

  initializeNotifications() {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission();
    }
  }

  createPreviewMessage(message) {
    const preview = document.createElement("div");
    preview.className = "chat-preview";
    preview.innerHTML = `
        <div class="chat-preview-content">${message.message}</div>
        <div class="chat-preview-time">${new Date(
          message.created_at
        ).toLocaleTimeString()}</div>
    `;
    document.body.appendChild(preview);

    // Auto-hide preview after 5 seconds
    setTimeout(() => {
      preview.style.display = "none";
    }, 5000);

    return preview;
  }
}

// Export for use in other scripts
window.ChatWidget = ChatWidget;
