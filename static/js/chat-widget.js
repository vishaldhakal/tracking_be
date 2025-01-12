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
    this.isOpen = false;

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
                width: 60px;
                height: 60px;
                border-radius: 30px;
                background: #2563eb;
                color: white;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .chat-toggle:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
            }
            .chat-badge {
                position: absolute;
                top: -8px;
                right: -8px;
                background: #ef4444;
                color: white;
                border-radius: 20px;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: 600;
                display: none;
                animation: pulse 2s infinite;
            }
            .chat-box {
                position: fixed;
                bottom: 100px;
                right: 20px;
                width: 380px;
                height: 600px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.15);
                display: none;
                flex-direction: column;
                transform-origin: bottom right;
                animation: slideIn 0.3s ease-out;
            }
            .chat-header {
                padding: 20px;
                background: #2563eb;
                border-radius: 16px 16px 0 0;
                color: white;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .chat-title {
                font-weight: 600;
                font-size: 16px;
                margin: 0;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .chat-title::before {
                content: '';
                display: inline-block;
                width: 8px;
                height: 8px;
                background: #4ade80;
                border-radius: 50%;
            }
            .chat-close {
                background: rgba(255,255,255,0.2);
                border: none;
                cursor: pointer;
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.3s ease;
            }
            .chat-close:hover {
                background: rgba(255,255,255,0.3);
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
                animation: slideIn 1s ease-out;
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
                0% { transform: translateY(20px) scale(0.95); opacity: 0; }
                100% { transform: translateY(0) scale(1); opacity: 1; }
            }
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }
        `;
    document.head.appendChild(styles);
  }

  createWidget() {
    const widget = document.createElement("div");
    widget.className = "chat-widget";
    widget.innerHTML = `
            <button class="chat-toggle" aria-label="Open chat">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                </svg>
                <span class="chat-badge">0</span>
            </button>
            <div class="chat-box">
                <div class="chat-header">
                    <h4 class="chat-title">Homebaba Support</h4>
                    <button class="chat-close" aria-label="Close chat">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
                <div class="chat-messages"></div>
                <div class="chat-input-container">
                    <input type="text" class="chat-input" placeholder="Type your message here...">
                    <button class="chat-send" aria-label="Send message">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 2L11 13"></path>
                            <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                        </svg>
                    </button>
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

      this.isOpen = !this.isOpen;
      chatBox.style.display = this.isOpen ? "flex" : "none";

      if (this.isOpen) {
        messagesContainer.innerHTML = "";
        Array.from(this.messages.values())
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
          .forEach((message) => this.appendMessage(message));

        badge.style.display = "none";
        badge.textContent = "0";
        toggle.classList.remove("has-new");
        input.focus();

        messagesContainer.scrollTop = messagesContainer.scrollHeight;
      }
    });

    closeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this.isOpen = false;
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
