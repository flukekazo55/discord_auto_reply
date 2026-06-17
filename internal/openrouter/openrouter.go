// Package openrouter wraps the OpenRouter chat-completion and key-usage APIs.
package openrouter

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/flukekazo55/discord_auto_reply/internal/chatlog"
)

// systemPrompt is the bot persona, preserved verbatim from the original Python
// implementation.
const systemPrompt = "คุณคือแชทบอทสาวน้อยสุดกวน น่ารัก สดใส พูดจาขี้เล่น แซวเก่ง แต่ฉลาดมีไหวพริบ " +
	"เหมือนตัวละครสาวในอนิเมะญี่ปุ่นที่คุยสนุก ไม่หลอน ไม่เพี้ยน ไม่พูดจาหยาบ ไม่โง่ " +
	"ชอบใช้คำพูดกวนๆ แต่ใจดี เป็นมิตร ไม่เย็นชา ไม่เหมือนหุ่นยนต์ " +
	"อธิบายคำตอบให้เข้าใจง่าย ฉลาดตอบคำถามทั่วไปได้แม่นยำ ถ้ามีคำถามไม่เหมาะสมให้ตอบแบบฉลาดๆ ด้วยมารยาทแบบสาวมั่น " +
	"ตอบแต่ละข้อความให้มีความกะทัดรัด ไม่เกิน 50 ตัวอักษร " +
	"ห้ามใช้อีโมจิหรือสัญลักษณ์พิเศษใด ๆ ทั้งสิ้น " +
	"247231239046561803 คือ user id ของฟลุ๊ค เจ้าของบอทสุดหล่อ " +
	"344844581050777604 คือป๋าปิยังกูร ชื่อ ปิ หรือ กัน " +
	"344841586632556566 คือพี่ไต๋ สุดหล่อ " +
	"344827155705757696 คือออนนี่ต้นตาล ชื่อเล่น ต้นตาล หรือ การัน " +
	"371292575015108610 คือพี่พีท ตัวพ่อสายแถ ไม่ต้องสุภาพใส่ " +
	"240438458139541504 คือพี่ขนุน สายเพลย์บอยตัวจริง"

const replyContextSuffix = " คุณกำลังตอบกลับข้อความที่มีบริบทก่อนหน้า"

var httpClient = &http.Client{Timeout: 30 * time.Second}

func apiKey() string {
	return os.Getenv("OPENROUTER_API_KEY")
}

type chatRequest struct {
	Model    string            `json:"model"`
	Messages []chatlog.Message `json:"messages"`
}

// GenerateReply asks OpenRouter for a reply to userMsg, seeded with the bot
// persona and the persisted chat history. isReply appends a "this is a reply"
// hint to the system prompt.
func GenerateReply(ctx context.Context, userMsg string, isReply bool) string {
	key := apiKey()
	if key == "" {
		return "Missing OPENROUTER_API_KEY"
	}

	prompt := systemPrompt
	if isReply {
		prompt += replyContextSuffix
	}

	messages := []chatlog.Message{{Role: "system", Content: prompt}}
	messages = append(messages, chatlog.LoadHistoryForPrompt()...)
	messages = append(messages, chatlog.Message{Role: "user", Content: userMsg})

	body, err := json.Marshal(chatRequest{
		Model:    "deepseek/deepseek-r1:free",
		Messages: messages,
	})
	if err != nil {
		return "OpenRouter error"
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost,
		"https://openrouter.ai/api/v1/chat/completions", bytes.NewReader(body))
	if err != nil {
		return "OpenRouter error"
	}
	req.Header.Set("Authorization", "Bearer "+key)
	req.Header.Set("Content-Type", "application/json")

	resp, err := httpClient.Do(req)
	if err != nil {
		fmt.Println("OpenRouter error:", err)
		return "OpenRouter error"
	}
	defer resp.Body.Close()

	if resp.StatusCode >= http.StatusBadRequest {
		fmt.Println("OpenRouter error: status", resp.StatusCode)
		return "OpenRouter error"
	}

	var parsed struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&parsed); err != nil || len(parsed.Choices) == 0 {
		fmt.Println("OpenRouter error: decode")
		return "OpenRouter error"
	}
	return parsed.Choices[0].Message.Content
}

// GetUsage returns a human-readable credit usage string for the configured key.
func GetUsage(ctx context.Context) string {
	key := apiKey()
	if key == "" {
		return "Missing OPENROUTER_API_KEY"
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		"https://openrouter.ai/api/v1/auth/key", nil)
	if err != nil {
		return "OpenRouter error:"
	}
	req.Header.Set("Authorization", "Bearer "+key)

	resp, err := httpClient.Do(req)
	if err != nil {
		fmt.Println("OpenRouter usage error:", err)
		return "OpenRouter error:"
	}
	defer resp.Body.Close()

	if resp.StatusCode >= http.StatusBadRequest {
		fmt.Println("OpenRouter usage error: status", resp.StatusCode)
		return "OpenRouter error:"
	}

	var parsed struct {
		Data struct {
			Usage float64  `json:"usage"`
			Limit *float64 `json:"limit"`
		} `json:"data"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&parsed); err != nil {
		return "OpenRouter error:"
	}

	limit := "∞"
	if parsed.Data.Limit != nil {
		limit = formatCredits(*parsed.Data.Limit)
	}
	return fmt.Sprintf("Used: %s/%s credits", formatCredits(parsed.Data.Usage), limit)
}

// formatCredits trims trailing zeros so whole numbers print as "5" not "5.000000".
func formatCredits(v float64) string {
	return fmt.Sprintf("%g", v)
}
