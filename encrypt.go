// Tips: go run *.go will print exit status, go build *.go and run with binary file will ignore it.
// vim: fdm=indent ts=4 sw=4 sts=4 expandtab
package main

import (
	"crypto/md5"
	b64 "encoding/base64"
	"encoding/hex"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	s "strings"
	"sync"
	"syscall"
	"time"
)

var P = fmt.Println

// => comman func {{{

const (
	IKEY  string = "-x6g6ZWm2G9g_vr0Bo.pOq3kRIxsZ6rm"
	KEY   string = "!@#$%^&*"
	CHARS string = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_~"
)

func GetOptVal(opt string) string {
	i := ArraySearch(os.Args, opt)
	if i == -1 || len(os.Args) == i+1 {
		return ""
	}
	val := os.Args[i+1]
	if val[:1] == "-" && len(val) == 2 {
		return ""
	}
	return val
}

func ArraySearch(vs []string, t string) int {
	for i, v := range vs {
		if v == t {
			return i
		}
	}
	return -1
}

func GetPathFromArgs(vs []string) string {
	path := ""
	for _, v := range vs {
		if ExistsPath(v) {
			return v
		}
	}
	return path
}

func ExistsPath(name string) bool {
	if _, err := os.Stat(name); err != nil {
		if os.IsNotExist(err) {
			return false
		}
	}
	return true
}

func GetStatTimes(name string) (atime, mtime time.Time, err error) {
	fi, err := os.Stat(name)
	if err != nil {
		return
	}
	mtime = fi.ModTime()
	stat := fi.Sys().(*syscall.Stat_t)
	atime = time.Unix(int64(stat.Atimespec.Sec), int64(stat.Atimespec.Nsec))
	return
}

func Base64Encode(text string) string {
	sEnc := b64.StdEncoding.EncodeToString([]byte(text))
	return sEnc
}

func Base64Decode(text string) string {
	sDec, _ := b64.StdEncoding.DecodeString(text)
	return string(sDec)
}

func GetMD5Hash(text string) string {
	hasher := md5.New()
	hasher.Write([]byte(text))
	return hex.EncodeToString(hasher.Sum(nil))
}

func SubsrReplace(subject string, replace string, start int, leng ...int) string {
	str := ""
	if len(leng) == 0 {
		str = subject[:start] + replace
	} else {
		length := leng[0]
		if length < 0 {
			str = subject[:start] + replace + subject[length:]
		} else {
			str = subject[:start] + replace + subject[start+length:]
		}
	}
	return str
}

func Decode(txt string) string {
	key := KEY
	chars := CHARS
	ikey := IKEY
	knum := 0
	tlen := len(txt)
	clen := len(CHARS)

	for _, c := range key {
		knum += int(c)
	}

	ch1 := string(txt[knum%tlen])
	nh1 := s.Index(chars, ch1)
	txt = SubsrReplace(txt, "", knum%tlen, 1)
	tlen -= 1
	ch2 := string(txt[nh1%tlen])
	nh2 := s.Index(chars, ch2)
	txt = SubsrReplace(txt, "", nh1%tlen, 1)
	tlen -= 1
	ch3 := string(txt[nh2%tlen])
	nh3 := s.Index(chars, ch3)
	txt = SubsrReplace(txt, "", nh2%tlen, 1)
	nhnum := nh1 + nh2 + nh3
	mdKey := GetMD5Hash(GetMD5Hash(GetMD5Hash(key+ch1)+ch2+ikey) + ch3)[nhnum%8 : nhnum%8+knum%8+16]
	tmp := ""
	k := 0
	klen := len(mdKey)

	for _, char := range txt {
		if k == klen {
			k = 0
		}
		ci := s.Index(chars, string(char))
		if ci < 0 {
			ci = 0
		}
		j := ci - nhnum - int(mdKey[k])
		k += 1
		for j < 0 {
			j += 64
		}
		if j < 0 {
			tmp += string(chars[j+clen])
		} else {
			tmp += string(chars[j])
		}
	}
	keys := []string{"-", "_", "."}
	values := []string{"+", "/", "="}
	for i, char := range keys {
		tmp = s.Replace(tmp, char, values[i], -1)
	}
	tmp = Base64Decode(tmp)
	r := regexp.MustCompile("[\000]")
	tmp = r.ReplaceAllString(tmp, "")
	return tmp
}

func Encode(txt string) string {
	key := KEY
	chars := CHARS
	ikey := IKEY

	nh1 := rand.Intn(64)
	nh2 := rand.Intn(64)
	nh3 := rand.Intn(64)

	ch1 := string(chars[nh1])
	ch2 := string(chars[nh2])
	ch3 := string(chars[nh3])
	nhnum := nh1 + nh2 + nh3
	knum := 0
	for _, c := range key {
		knum += int(c)
	}
	mdKey := GetMD5Hash(GetMD5Hash(GetMD5Hash(key+ch1)+ch2+ikey) + ch3)[nhnum%8 : nhnum%8+knum%8+16]
	txt = Base64Encode(txt)

	keys := []string{"-", "_", "."}
	values := []string{"+", "/", "="}
	for i, char := range keys {
		txt = s.Replace(txt, char, values[i], -1)
	}

	tmp := ""
	k := 0
	j := 0
	klen := len(mdKey)
	clen := len(CHARS)

	for _, char := range txt {
		if k == klen {
			k = 0
		}
		ci := s.Index(chars, string(char))
		if ci < 0 {
			ci = 0
		}
		j = (nhnum + ci + int(mdKey[k])) % 64
		k += 1
		if j < 0 {
			tmp += string(chars[j+clen])
		} else {
			tmp += string(chars[j])
		}
	}

	tmplen := len(tmp)
	tmplen += 1
	tmp = SubsrReplace(tmp, ch3, nh2%tmplen, 0)
	tmplen += 1
	tmp = SubsrReplace(tmp, ch2, nh1%tmplen, 0)
	tmplen += 1
	tmp = SubsrReplace(tmp, ch1, knum%tmplen, 0)
	return tmp
}

func EncodeFilename(filename string) string {
	basename := filepath.Base(filename)
	dirname := filepath.Dir(filename)
	basename = Encode(basename)
	filename = filepath.Join(dirname, basename)
	return filename
}

func DecodeFilename(filename string) string {
	basename := filepath.Base(filename)
	dirname := filepath.Dir(filename)
	basename = Decode(basename)
	filename = filepath.Join(dirname, basename)
	return filename
}

func Encrypt(file string, action string, encfilename bool) error {
	arrps := [3][2]int{{0, 20}, {5, 30}, {20, 10}}
	if action == "decrypt" {
		arrps = [3][2]int{{10, 20}, {30, 5}, {20, 0}}
	}

	atime, mtime, err := GetStatTimes(file)
	if err != nil {
		P(err)
	}

	f, err := os.OpenFile(file, os.O_RDWR, 0755)
	if err != nil {
		P(err)
	}

	for _, pos := range arrps {
		pos1 := pos[0]
		pos2 := pos[1]
		f.Seek(int64(pos1), 0)
		char1 := make([]byte, 1)
		f.Read(char1)
		f.Seek(int64(pos2), 0)
		char2 := make([]byte, 1)
		f.Read(char2)

		f.Seek(int64(pos1), 0)
		f.Write(char2)
		f.Seek(int64(pos2), 0)
		f.Write(char1)

	}

	if err := f.Close(); err != nil {
		P(err)
	}

	if err := os.Chtimes(file, atime, mtime); err != nil {
		P(err)
	}

	if encfilename {
		nfile := ""
		if action == "decrypt" {
			nfile = DecodeFilename(file)
		} else {
			nfile = EncodeFilename(file)
		}
		os.Rename(file, nfile)
	}

	return nil
}

func GetFilelist(path string) []string {
	filelist := []string{}
	filepath.Walk(path, func(path string, f os.FileInfo, err error) error {
		if !f.IsDir() {
			filelist = append(filelist, path)
		}
		return nil
	})
	return filelist
}

// => common func block end }}}

// => pool block {{{
type Pool struct {
	queue chan int
	wg    *sync.WaitGroup
}

func NewPool(cap, total int) *Pool {
	if cap < 1 {
		cap = 1
	}
	p := &Pool{
		queue: make(chan int, cap),
		wg:    new(sync.WaitGroup),
	}
	p.wg.Add(total)
	return p
}

func (p *Pool) AddOne() {
	p.queue <- 1
}

func (p *Pool) DelOne() {
	<-p.queue
	p.wg.Done()
}

// => pool block end }}}
var Usage = func(code int, msg ...string) {
	if len(msg) > 0 {
		fmt.Fprintf(os.Stdin, "\x1b[38;5;1m* %s\x1b[0m\n", msg[0])
	}
	fmt.Fprintf(os.Stdin, "Usage: %s [options] file/dir\n\n", filepath.Base(os.Args[0]))
	fmt.Println(" -e      encrypt file")
	fmt.Println(" -d      decrypt file")
	fmt.Println(" -w      worker count, default: 50")
	fmt.Println(" -x      dont encode filename")
	fmt.Println(" -h      show command usage")
	os.Exit(code)
}

func main() {
	ts := time.Now()

	cap := 50
	path := GetPathFromArgs(os.Args[1:])
	action := "encrypt"
	encfilename := true

	if ArraySearch(os.Args, "-h") > -1 {
		Usage(0)
	}

	if path == "" {
		Usage(2, "path is not exists, please check 'file/dir' param")
	}

	if ArraySearch(os.Args, "-d") > -1 {
		action = "decrypt"
	}

	if ArraySearch(os.Args, "-x") > -1 {
		encfilename = false
	}

	if wc := GetOptVal("-w"); wc != "" {
		nwc, _ := strconv.Atoi(wc)
		if nwc > 0 {
			cap = nwc
		}
	}

	filelist := GetFilelist(path)
	pool := NewPool(cap, len(filelist))
	for _, v := range filelist {
		go func(file string) {
			pool.AddOne()
			err := Encrypt(file, action, encfilename)
			if nil != err {
				P(err)
			}
			pool.DelOne()
		}(v)
	}
	pool.wg.Wait()

	te := time.Now()
	fmt.Printf("release time is: %.2f\n", te.Sub(ts).Seconds())
}
