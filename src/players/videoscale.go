package players

import (
	"encoding/json"
	"log"
	"os/exec"
)

func getVideoSize(filepath string) (int, int) {
	cmd := exec.Command("ffprobe", "-v", "error", "-print_format", "json", "-select_streams", "v:0", "-show_entries", "stream=width,height", filepath)
	output, err := cmd.Output()
	if err != nil {
		return 0, 0
	}
	var outputMap map[string]any
	if json.Unmarshal(output, &outputMap) != nil {
		return 0, 0
	}
	streams := outputMap["streams"].([]any)
	stream := streams[0]
	streamMap := stream.(map[string]any)
	width := int(streamMap["width"].(float64))
	height := int(streamMap["height"].(float64))
	return width, height
}

func getVideoScale(filepath string, windowW, windowH int) float64 {
	videoW, videoH := getVideoSize(filepath)
	log.Println("Video size: ", videoW, "x", videoH, "; window size: ", windowW, "x", windowH)

	widthRatio := float64(windowW) / float64(videoW)
	heightRatio := float64(windowH) / float64(videoH)

	return min(widthRatio, heightRatio) * 2 // Display resolution?
}
