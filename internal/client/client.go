package client

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

type NetBoxClient interface {
	Get(endpoint string, params map[string]interface{}) (interface{}, error)
	Create(endpoint string, data map[string]interface{}) (map[string]interface{}, error)
	Update(endpoint string, id int, data map[string]interface{}) (map[string]interface{}, error)
	Delete(endpoint string, id int) (bool, error)
	BulkCreate(endpoint string, data []map[string]interface{}) ([]map[string]interface{}, error)
	BulkUpdate(endpoint string, data []map[string]interface{}) ([]map[string]interface{}, error)
	BulkDelete(endpoint string, ids []int) (bool, error)
}

type NetBoxRestClient struct {
	BaseURL   string
	APIURL    string
	Token     string
	VerifySSL bool
	Client    *http.Client
}

func NewNetBoxRestClient(url, token string, verifySSL bool) *NetBoxRestClient {
	baseURL := strings.TrimRight(url, "/")
	apiURL := fmt.Sprintf("%s/api", baseURL)

	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: !verifySSL},
	}
	client := &http.Client{Transport: tr}

	return &NetBoxRestClient{
		BaseURL:   baseURL,
		APIURL:    apiURL,
		Token:     token,
		VerifySSL: verifySSL,
		Client:    client,
	}
}

func (c *NetBoxRestClient) buildURL(endpoint string, id *int) string {
	endpoint = strings.Trim(endpoint, "/")
	if id != nil {
		return fmt.Sprintf("%s/%s/%d/", c.APIURL, endpoint, *id)
	}
	return fmt.Sprintf("%s/%s/", c.APIURL, endpoint)
}

func (c *NetBoxRestClient) makeRequest(method, url string, body interface{}, params map[string]interface{}) (interface{}, error) {
	var reqBody io.Reader
	if body != nil {
		jsonData, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonData)
	}

	req, err := http.NewRequest(method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", fmt.Sprintf("Token %s", c.Token))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	if params != nil && len(params) > 0 {
		q := req.URL.Query()
		for key, value := range params {
			switch v := value.(type) {
			case string:
				q.Add(key, v)
			case int:
				q.Add(key, fmt.Sprintf("%d", v))
			case []string:
				q.Add(key, strings.Join(v, ","))
			case bool:
				if v {
					q.Add(key, "1")
				} else {
					q.Add(key, "0")
				}
			default:
				q.Add(key, fmt.Sprintf("%v", v))
			}
		}
		req.URL.RawQuery = q.Encode()
	}

	resp, err := c.Client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("API request failed with status %d: %s", resp.StatusCode, string(respBody))
	}

	if method == "DELETE" {
		return resp.StatusCode == 204, nil
	}

	var result interface{}
	if len(respBody) > 0 {
		if err := json.Unmarshal(respBody, &result); err != nil {
			return nil, fmt.Errorf("failed to unmarshal response: %w", err)
		}
	}

	return result, nil
}

func (c *NetBoxRestClient) Get(endpoint string, params map[string]interface{}) (interface{}, error) {
	url := c.buildURL(endpoint, nil)
	return c.makeRequest("GET", url, nil, params)
}

func (c *NetBoxRestClient) GetByID(endpoint string, id int, params map[string]interface{}) (interface{}, error) {
	url := c.buildURL(endpoint, &id)
	return c.makeRequest("GET", url, nil, params)
}

func (c *NetBoxRestClient) Create(endpoint string, data map[string]interface{}) (map[string]interface{}, error) {
	url := c.buildURL(endpoint, nil)
	result, err := c.makeRequest("POST", url, data, nil)
	if err != nil {
		return nil, err
	}
	return result.(map[string]interface{}), nil
}

func (c *NetBoxRestClient) Update(endpoint string, id int, data map[string]interface{}) (map[string]interface{}, error) {
	url := c.buildURL(endpoint, &id)
	result, err := c.makeRequest("PATCH", url, data, nil)
	if err != nil {
		return nil, err
	}
	return result.(map[string]interface{}), nil
}

func (c *NetBoxRestClient) Delete(endpoint string, id int) (bool, error) {
	url := c.buildURL(endpoint, &id)
	result, err := c.makeRequest("DELETE", url, nil, nil)
	if err != nil {
		return false, err
	}
	return result.(bool), nil
}

func (c *NetBoxRestClient) BulkCreate(endpoint string, data []map[string]interface{}) ([]map[string]interface{}, error) {
	url := fmt.Sprintf("%sbulk/", c.buildURL(endpoint, nil))
	result, err := c.makeRequest("POST", url, data, nil)
	if err != nil {
		return nil, err
	}
	return result.([]map[string]interface{}), nil
}

func (c *NetBoxRestClient) BulkUpdate(endpoint string, data []map[string]interface{}) ([]map[string]interface{}, error) {
	url := fmt.Sprintf("%sbulk/", c.buildURL(endpoint, nil))
	result, err := c.makeRequest("PATCH", url, data, nil)
	if err != nil {
		return nil, err
	}
	return result.([]map[string]interface{}), nil
}

func (c *NetBoxRestClient) BulkDelete(endpoint string, ids []int) (bool, error) {
	url := fmt.Sprintf("%sbulk/", c.buildURL(endpoint, nil))
	data := make([]map[string]interface{}, len(ids))
	for i, id := range ids {
		data[i] = map[string]interface{}{"id": id}
	}
	result, err := c.makeRequest("DELETE", url, data, nil)
	if err != nil {
		return false, err
	}
	return result.(bool), nil
}
