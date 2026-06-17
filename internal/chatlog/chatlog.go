// Package chatlog persists Discord chat interactions to a JSONL file and reads
// them back for AI prompt context and the /fhistory command.
//
// On Vercel the log lives in /tmp, which is ephemeral: it survives only for the
// lifetime of a warm serverless instance and is wiped on cold starts and
// redeploys. This matches the previous Python behavior.
package chatlog

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

// Entry is a single persisted chat exchange.
type Entry struct {
	Timestamp   string `json:"timestamp"`
	UserID      string `json:"user_id"`
	Username    string `json:"username"`
	UserMessage string `json:"user_message"`
	BotReply    string `json:"bot_reply"`
}

// Message is one OpenRouter chat-completion message.
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// filePath resolves where the chat log lives, mirroring the Python logic:
// CHAT_LOG_PATH override, then /tmp on Vercel, then a local file.
func filePath() string {
	if p := os.Getenv("CHAT_LOG_PATH"); p != "" {
		return p
	}
	if os.Getenv("VERCEL") != "" {
		return "/tmp/chat_log.jsonl"
	}
	return filepath.Join(".", "chat_log.jsonl")
}

func newScanner(f *os.File) *bufio.Scanner {
	s := bufio.NewScanner(f)
	// Allow long lines (default is 64KB); chat replies can be lengthy.
	s.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	return s
}

// Save appends a single exchange to the log file.
func Save(userID, username, userMsg, botReply string) error {
	entry := Entry{
		Timestamp:   time.Now().UTC().Format(time.RFC3339),
		UserID:      userID,
		Username:    username,
		UserMessage: userMsg,
		BotReply:    botReply,
	}
	data, err := json.Marshal(entry)
	if err != nil {
		return err
	}

	f, err := os.OpenFile(filePath(), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = f.Write(append(data, '\n'))
	return err
}

// LoadHistoryForPrompt returns the full log flattened into alternating
// user/assistant messages for use as AI prompt context.
func LoadHistoryForPrompt() []Message {
	var history []Message

	f, err := os.Open(filePath())
	if err != nil {
		return history
	}
	defer f.Close()

	scanner := newScanner(f)
	for scanner.Scan() {
		var e Entry
		if err := json.Unmarshal(scanner.Bytes(), &e); err != nil {
			continue
		}
		history = append(history,
			Message{Role: "user", Content: e.UserMessage},
			Message{Role: "assistant", Content: e.BotReply},
		)
	}
	return history
}

// GetUserHistory returns up to max of the most recent exchanges for a user,
// newest first, formatted for display.
func GetUserHistory(userID string, max int) []string {
	f, err := os.Open(filePath())
	if err != nil {
		return []string{"No chat history found."}
	}
	defer f.Close()

	var entries []Entry
	scanner := newScanner(f)
	for scanner.Scan() {
		var e Entry
		if err := json.Unmarshal(scanner.Bytes(), &e); err != nil {
			continue
		}
		entries = append(entries, e)
	}

	var out []string
	for i := len(entries) - 1; i >= 0; i-- {
		if entries[i].UserID == userID {
			out = append(out, "- "+entries[i].UserMessage+" ➜ "+entries[i].BotReply)
			if len(out) >= max {
				break
			}
		}
	}
	if len(out) == 0 {
		return []string{"No chat history found."}
	}
	return out
}
