package main

import (
    "bytes"
    "encoding/base64"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
)

func main() {
    url := getenv("HOLOBIT_API_URL", "http://localhost:8000")
    user := getenv("HOLOBIT_USER", "user")
    pass := getenv("HOLOBIT_PASSWORD", "pass")
    auth := base64.StdEncoding.EncodeToString([]byte(user + ":" + pass))

    codePayload := map[string]string{"code": "print(\"Hola Holobit\")"}
    jobID := post(url+"/compile", codePayload, auth)
    fmt.Println("Job ID:", jobID)

    result := post(url+"/execute", map[string]string{"job_id": jobID}, auth)
    fmt.Println("Resultado:", result)
}

func getenv(key, def string) string {
    if v, ok := os.LookupEnv(key); ok {
        return v
    }
    return def
}

func post(url string, payload map[string]string, auth string) string {
    data, _ := json.Marshal(payload)
    req, _ := http.NewRequest("POST", url, bytes.NewBuffer(data))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("Authorization", "Basic "+auth)

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    body, _ := ioutil.ReadAll(resp.Body)
    var res map[string]string
    json.Unmarshal(body, &res)
    if v, ok := res["job_id"]; ok {
        return v
    }
    if v, ok := res["result"]; ok {
        return v
    }
    return string(body)
}
