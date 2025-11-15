package config

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

type Settings struct {
	NetBoxURL   string
	NetBoxToken string
	Transport   string
	Host        string
	Port        int
	VerifySSL   bool
	LogLevel    string
}

func NewSettings() *Settings {
	return &Settings{
		Transport: "stdio",
		Host:      "127.0.0.1",
		Port:      8000,
		VerifySSL: true,
		LogLevel:  "INFO",
	}
}

func LoadEnvFile() error {
	paths := []string{
		".env",
		"../.env",
		filepath.Join(os.Getenv("HOME"), ".env"),
	}

	for _, path := range paths {
		if _, err := os.Stat(path); err == nil {
			if err := godotenv.Load(path); err == nil {
				log.Printf("Loaded environment variables from: %s", path)
				return nil
			}
		}
	}
	return nil
}

func (s *Settings) LoadFromEnv() {
	if url := os.Getenv("NETBOX_URL"); url != "" {
		s.NetBoxURL = url
	}
	if token := os.Getenv("NETBOX_TOKEN"); token != "" {
		s.NetBoxToken = token
	}
	if transport := os.Getenv("TRANSPORT"); transport != "" {
		s.Transport = transport
	}
	if host := os.Getenv("HOST"); host != "" {
		s.Host = host
	}
	if port := os.Getenv("PORT"); port != "" {
		if p, err := strconv.Atoi(port); err == nil {
			s.Port = p
		}
	}
	if verifySSL := os.Getenv("VERIFY_SSL"); verifySSL != "" {
		s.VerifySSL = strings.ToLower(verifySSL) == "true" || verifySSL == "1"
	}
	if logLevel := os.Getenv("LOG_LEVEL"); logLevel != "" {
		s.LogLevel = strings.ToUpper(logLevel)
	}
}

func (s *Settings) LoadFromCLI() {
	netboxURL := flag.String("netbox-url", "", "Base URL of the NetBox instance")
	netboxToken := flag.String("netbox-token", "", "API token for NetBox authentication")
	transport := flag.String("transport", "", "MCP transport protocol (stdio or http)")
	host := flag.String("host", "", "Host address for HTTP server")
	port := flag.Int("port", 0, "Port for HTTP server")
	verifySSL := flag.Bool("verify-ssl", true, "Verify SSL certificates")
	noVerifySSL := flag.Bool("no-verify-ssl", false, "Disable SSL certificate verification")
	logLevel := flag.String("log-level", "", "Logging verbosity level")

	flag.Parse()

	if *netboxURL != "" {
		s.NetBoxURL = *netboxURL
	}
	if *netboxToken != "" {
		s.NetBoxToken = *netboxToken
	}
	if *transport != "" {
		s.Transport = *transport
	}
	if *host != "" {
		s.Host = *host
	}
	if *port != 0 {
		s.Port = *port
	}
	if *noVerifySSL {
		s.VerifySSL = false
	} else if flag.Lookup("verify-ssl").Value.String() != "true" {
		s.VerifySSL = *verifySSL
	}
	if *logLevel != "" {
		s.LogLevel = strings.ToUpper(*logLevel)
	}
}

func (s *Settings) Validate() error {
	if s.NetBoxURL == "" {
		return fmt.Errorf("NETBOX_URL is required")
	}
	if s.NetBoxToken == "" {
		return fmt.Errorf("NETBOX_TOKEN is required")
	}
	if !strings.HasPrefix(s.NetBoxURL, "http://") && !strings.HasPrefix(s.NetBoxURL, "https://") {
		return fmt.Errorf("NETBOX_URL must include scheme (http:// or https://)")
	}
	if s.Transport != "stdio" && s.Transport != "http" {
		return fmt.Errorf("TRANSPORT must be 'stdio' or 'http', got '%s'", s.Transport)
	}
	if s.Port < 1 || s.Port > 65535 {
		return fmt.Errorf("PORT must be between 1 and 65535, got %d", s.Port)
	}
	validLogLevels := map[string]bool{
		"DEBUG": true, "INFO": true, "WARNING": true, "ERROR": true, "CRITICAL": true,
	}
	if !validLogLevels[s.LogLevel] {
		return fmt.Errorf("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")
	}
	return nil
}

func (s *Settings) GetEffectiveConfigSummary() map[string]interface{} {
	summary := map[string]interface{}{
		"netbox_url":   s.NetBoxURL,
		"netbox_token": "***REDACTED***",
		"transport":    s.Transport,
		"verify_ssl":   s.VerifySSL,
		"log_level":    s.LogLevel,
	}
	if s.Transport == "http" {
		summary["host"] = s.Host
		summary["port"] = s.Port
	} else {
		summary["host"] = "N/A"
		summary["port"] = "N/A"
	}
	return summary
}

func ConfigureLogging(logLevel string) {
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)

	switch logLevel {
	case "DEBUG":
		log.SetPrefix("[DEBUG] ")
	case "INFO":
		log.SetPrefix("[INFO] ")
	case "WARNING":
		log.SetPrefix("[WARNING] ")
	case "ERROR":
		log.SetPrefix("[ERROR] ")
	case "CRITICAL":
		log.SetPrefix("[CRITICAL] ")
	default:
		log.SetPrefix("[INFO] ")
	}
}
