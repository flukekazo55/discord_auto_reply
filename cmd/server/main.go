// Command server is the HTTP entrypoint Vercel builds and runs. Vercel's Go
// web-server detection looks for cmd/server/main.go (among a few known paths),
// compiles it, and proxies all incoming requests to the address given by $PORT.
//
// The same binary runs locally: it listens on $PORT (default 3000).
package main

import (
	"log"
	"net/http"
	"os"

	"github.com/flukekazo55/discord_auto_reply/internal/handler"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "3000"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/", handler.Handler)

	addr := ":" + port
	log.Printf("Discord interactions server listening on %s", addr)
	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatal(err)
	}
}
