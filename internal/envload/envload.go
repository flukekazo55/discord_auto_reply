// Package envload provides a minimal, dependency-free .env file loader so local
// development matches the behavior of the previous python-dotenv setup. On Vercel
// environment variables come from the project settings, so the missing-file case
// is silently ignored.
package envload

import (
	"bufio"
	"os"
	"strings"
)

// Load reads key=value pairs from the given .env file and sets them as process
// environment variables. Existing variables are never overwritten. A missing
// file is not an error.
func Load(path string) {
	f, err := os.Open(path)
	if err != nil {
		return
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		key, value, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		key = strings.TrimSpace(key)
		value = strings.Trim(strings.TrimSpace(value), `"'`)

		if key == "" {
			continue
		}
		if _, exists := os.LookupEnv(key); !exists {
			os.Setenv(key, value)
		}
	}
}
