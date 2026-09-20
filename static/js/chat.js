// ==========================================================================
// Virtual AI Tutor - Chat Interface Engine
// ==========================================================================

let activeConversationId = window.CURRENT_CONVERSATION_ID || null;

document.addEventListener("DOMContentLoaded", () => {
    const chatInput = document.getElementById("chatInput");
    const btnSend = document.getElementById("btnSendChat");
    const messagesContainer = document.getElementById("chatMessagesContainer");
    const btnNewChat = document.getElementById("btnNewChat");
    const toggleSidebarBtn = document.getElementById("toggleChatSidebarBtn");
    const chatSidebar = document.getElementById("chatSidebar");
    const chatSearchInput = document.getElementById("chatSearchInput");

    // Configure Marked.js
    if (window.marked) {
        marked.setOptions({
            breaks: true,
            gfm: true,
            highlight: function (code, lang) {
                if (window.hljs && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return code;
            },
        });
    }

    scrollToBottom();

    // Auto-resize textarea as user types
    if (chatInput) {
        chatInput.addEventListener("input", () => {
            chatInput.style.height = "auto";
            chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
        });

        // Keydown: Enter sends message, Shift+Enter inserts newline
        chatInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    if (btnSend) {
        btnSend.addEventListener("click", () => {
            sendMessage();
        });
    }

    // Toggle Chat History Sub-Sidebar
    if (toggleSidebarBtn && chatSidebar) {
        toggleSidebarBtn.addEventListener("click", () => {
            chatSidebar.classList.toggle("collapsed");
        });
    }

    // New Chat Button
    if (btnNewChat) {
        btnNewChat.addEventListener("click", () => {
            startNewChat();
        });
    }

    // Conversation Search Filter
    if (chatSearchInput) {
        chatSearchInput.addEventListener("input", (e) => {
            const query = e.target.value.toLowerCase().trim();
            const items = document.querySelectorAll(".chat-item");
            items.forEach((item) => {
                const title = item.querySelector(".chat-item-title").textContent.toLowerCase();
                if (title.includes(query)) {
                    item.style.display = "flex";
                } else {
                    item.style.display = "none";
                }
            });
        });
    }
});

// Scroll messages thread to bottom
function scrollToBottom() {
    const container = document.getElementById("chatMessagesContainer");
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// Global function to insert suggested prompt into chat
window.insertPrompt = function (text) {
    const chatInput = document.getElementById("chatInput");
    if (chatInput) {
        chatInput.value = text;
        chatInput.focus();
        sendMessage();
    }
};

// Send Message Handler
async function sendMessage() {
    const chatInput = document.getElementById("chatInput");
    const btnSend = document.getElementById("btnSendChat");
    const container = document.getElementById("chatMessagesContainer");
    const welcomeState = document.getElementById("chatWelcomeState");
    const question = chatInput.value.trim();

    if (!question) return;

    // If no active conversation exists, create one first
    if (!activeConversationId) {
        try {
            const newChatRes = await fetch("/api/chat/new", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: "New Conversation" }),
            });
            const newChatData = await newChatRes.json();
            if (newChatData.success) {
                activeConversationId = newChatData.id;
                window.history.replaceState(null, "", `/chat/${activeConversationId}`);
            }
        } catch (err) {
            console.error("Failed to create conversation:", err);
            return;
        }
    }

    // Hide welcome state if visible
    if (welcomeState) {
        welcomeState.style.display = "none";
    }

    // 1. Append User Message Bubble
    appendMessage("user", question);

    // Reset input
    chatInput.value = "";
    chatInput.style.height = "auto";
    chatInput.disabled = true;
    btnSend.disabled = true;

    // 2. Append Typing Indicator
    const typingId = appendTypingIndicator();
    scrollToBottom();

    // 3. Post question to backend RAG & AI Provider
    try {
        const response = await fetch(`/api/chat/${activeConversationId}/message`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question }),
        });

        const data = await response.json();

        // Remove typing indicator
        removeTypingIndicator(typingId);

        if (data.success) {
            // Update chat title in header if updated
            if (data.chat_title) {
                const titleElem = document.getElementById("currentChatTitle");
                if (titleElem) titleElem.textContent = data.chat_title;
            }

            // Append Assistant Message
            appendMessage(
                "assistant",
                data.content,
                data.message_id,
                data.is_grounded,
                data.sources
            );

            // Render Follow-up Chips
            renderFollowups(data.suggested_followups);
        } else {
            appendMessage("assistant", "⚠️ " + (data.error || "Unable to generate answer. Please try again."));
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        appendMessage("assistant", "⚠️ Network error communicating with the AI Tutor service. Please check your connection.");
        console.error("Chat error:", error);
    } finally {
        chatInput.disabled = false;
        btnSend.disabled = false;
        chatInput.focus();
        scrollToBottom();
    }
}

// Append message bubble to DOM
function appendMessage(sender, content, messageId = null, isGrounded = false, sources = []) {
    const container = document.getElementById("chatMessagesContainer");
    const wrapper = document.createElement("div");
    wrapper.className = `message-bubble-wrapper message-${sender}`;
    if (messageId) wrapper.setAttribute("data-message-id", messageId);

    // Avatar
    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    if (sender === "user") {
        avatar.textContent = "U";
    } else {
        avatar.innerHTML = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
        `;
    }
    wrapper.appendChild(avatar);

    // Bubble
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const senderName = document.createElement("div");
    senderName.className = "message-sender-name";
    senderName.textContent = sender === "user" ? "You" : "Virtual AI Tutor";
    bubble.appendChild(senderName);

    // Grounded Sources Drawer
    if (sender === "assistant" && isGrounded && sources && sources.length > 0) {
        const sourcesDrawer = document.createElement("div");
        sourcesDrawer.className = "grounded-sources-drawer";

        const pill = document.createElement("div");
        pill.className = "sources-pill";
        pill.innerHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
            </svg>
            <span>Grounded in Course Material (${sources.length} references) &darr;</span>
        `;

        const dropdown = document.createElement("div");
        dropdown.className = "sources-dropdown";
        sources.forEach((src) => {
            const card = document.createElement("div");
            card.className = "source-card-mini";
            card.innerHTML = `
                <div class="source-card-title">${escapeHtml(src.title)} (${escapeHtml(src.subject)})</div>
                <div class="source-card-snippet">${escapeHtml(src.snippet)}</div>
            `;
            dropdown.appendChild(card);
        });

        pill.addEventListener("click", () => {
            dropdown.classList.toggle("open");
        });

        sourcesDrawer.appendChild(pill);
        sourcesDrawer.appendChild(dropdown);
        bubble.appendChild(sourcesDrawer);
    }

    // Message Body
    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content markdown-body";

    if (window.marked && sender === "assistant") {
        contentDiv.innerHTML = marked.parse(content);
        // Trigger code highlight
        if (window.hljs) {
            contentDiv.querySelectorAll("pre code").forEach((el) => {
                hljs.highlightElement(el);
            });
        }
    } else {
        contentDiv.textContent = content;
    }
    bubble.appendChild(contentDiv);

    // Assistant Action Bar
    if (sender === "assistant") {
        const actionsBar = document.createElement("div");
        actionsBar.className = "message-actions-bar";
        actionsBar.innerHTML = `
            <button class="btn-action-copy" title="Copy answer" onclick="copyMessageText(this)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <span>Copy</span>
            </button>
            <button class="btn-action-rating" title="Helpful" onclick="rateMessage(${activeConversationId}, ${messageId}, 'helpful', this)">
                &check; Helpful
            </button>
            <button class="btn-action-rating" title="Not Helpful" onclick="rateMessage(${activeConversationId}, ${messageId}, 'unhelpful', this)">
                &cross; Not Helpful
            </button>
        `;
        bubble.appendChild(actionsBar);
    }

    wrapper.appendChild(bubble);
    container.appendChild(wrapper);
    scrollToBottom();
}

// Typing indicator helper
function appendTypingIndicator() {
    const container = document.getElementById("chatMessagesContainer");
    const id = "typing_" + Date.now();
    const wrapper = document.createElement("div");
    wrapper.id = id;
    wrapper.className = "message-bubble-wrapper message-assistant";
    wrapper.innerHTML = `
        <div class="message-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
        </div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <span style="font-size: 12px; color: var(--text-muted); margin-left: 8px;">Consulting course notes & formulating explanation...</span>
            </div>
        </div>
    `;
    container.appendChild(wrapper);
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Render dynamic suggested follow-up questions
function renderFollowups(followups) {
    const bar = document.getElementById("followupBar");
    const container = document.getElementById("followupChips");
    if (!bar || !container || !followups || followups.length === 0) return;

    container.innerHTML = "";
    followups.forEach((f) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "followup-chip";
        chip.textContent = f;
        chip.addEventListener("click", () => {
            insertPrompt(f);
            bar.style.display = "none";
        });
        container.appendChild(chip);
    });

    bar.style.display = "flex";
}

// Copy message text to clipboard
window.copyMessageText = function (btn) {
    const bubble = btn.closest(".message-bubble");
    const content = bubble.querySelector(".message-content").innerText;
    navigator.clipboard.writeText(content).then(() => {
        const span = btn.querySelector("span");
        const orig = span.textContent;
        span.textContent = "Copied!";
        setTimeout(() => { span.textContent = orig; }, 2000);
    });
};

// Rate message helpful/unhelpful
window.rateMessage = async function (convId, msgId, rating, btn) {
    if (!convId || !msgId) return;
    try {
        const res = await fetch(`/api/chat/${convId}/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message_id: msgId, rating: rating }),
        });
        const data = await res.json();
        if (data.success) {
            const bar = btn.parentElement;
            bar.querySelectorAll(".btn-action-rating").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
        }
    } catch (err) {
        console.error("Rating error:", err);
    }
};

// Start New Chat
async function startNewChat() {
    try {
        const res = await fetch("/api/chat/new", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ title: "New Conversation" }),
        });
        const data = await res.json();
        if (data.success) {
            window.location.href = `/chat/${data.id}`;
        }
    } catch (err) {
        console.error("Error creating new chat:", err);
    }
}

// Rename conversation modal handler
let renameChatId = null;
window.renameChat = function (id, currentTitle) {
    renameChatId = id;
    const modal = document.getElementById("renameModal");
    const input = document.getElementById("renameInput");
    if (modal && input) {
        input.value = currentTitle;
        modal.style.display = "flex";
        input.focus();
    }
};

window.closeRenameModal = function () {
    const modal = document.getElementById("renameModal");
    if (modal) modal.style.display = "none";
};

const btnSaveRename = document.getElementById("btnSaveRename");
if (btnSaveRename) {
    btnSaveRename.addEventListener("click", async () => {
        const input = document.getElementById("renameInput");
        const newTitle = input.value.trim();
        if (!newTitle || !renameChatId) return;

        try {
            const res = await fetch(`/api/chat/${renameChatId}/rename`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: newTitle }),
            });
            const data = await res.json();
            if (data.success) {
                // Update in sidebar DOM
                const item = document.querySelector(`.chat-item[data-chat-id="${renameChatId}"] .chat-item-title`);
                if (item) item.textContent = data.title;
                if (renameChatId === activeConversationId) {
                    const titleElem = document.getElementById("currentChatTitle");
                    if (titleElem) titleElem.textContent = data.title;
                }
                closeRenameModal();
            }
        } catch (err) {
            console.error("Rename error:", err);
        }
    });
}

// Delete chat
window.deleteChat = async function (id) {
    if (!confirm("Are you sure you want to delete this conversation?")) return;
    try {
        const res = await fetch(`/api/chat/${id}/delete`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });
        const data = await res.json();
        if (data.success) {
            if (id === activeConversationId) {
                window.location.href = "/chat";
            } else {
                const item = document.querySelector(`.chat-item[data-chat-id="${id}"]`);
                if (item) item.remove();
            }
        }
    } catch (err) {
        console.error("Delete error:", err);
    }
};

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
