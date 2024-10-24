#!/usr/bin/env php
<?php
class FileSafe
{
    const KEY = "!@#$%^&*";
    const IKEY = "-x6g6ZWm2G9g_vr0Bo.pOq3kRIxsZ6rm";
    const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.";
    
    static function StrDecrypt($txt)
    {
        $key = self::KEY;
        $chars = self::CHARS;
        $ikey = self::IKEY;
        $knum = 0;$i = 0;
        $tlen = strlen($txt);
        while(isset($key[$i])) $knum +=ord($key[$i++]);
        $ch1 = $txt[$knum % $tlen];
        $nh1 = strpos($chars,$ch1);
        $txt = substr_replace($txt,'',$knum % $tlen--,1);
        $ch2 = $txt[$nh1 % $tlen];
        $nh2 = strpos($chars,$ch2);
        $txt = substr_replace($txt,'',$nh1 % $tlen--,1);
        $ch3 = $txt[$nh2 % $tlen];
        $nh3 = strpos($chars,$ch3);
        $txt = substr_replace($txt,'',$nh2 % $tlen--,1);
        $nhnum = $nh1 + $nh2 + $nh3;
        $mdKey = substr(md5(md5(md5($key.$ch1).$ch2.$ikey).$ch3),$nhnum % 8,$knum % 8 + 16);
        $tmp = '';
        $j=0; $k = 0;
        $tlen = strlen($txt);
        $klen = strlen($mdKey);
        for ($i=0; $i<$tlen; $i++) {
            $k = $k == $klen ? 0 : $k;
            $j = strpos($chars,$txt[$i])-$nhnum - ord($mdKey[$k++]);
            while ($j<0) $j+=64;
            $tmp .= $chars[$j];
        }
        $tmp = str_replace(array('-','_','.'),array('+','/','='),$tmp);
        $tmp = base64_decode($tmp);
        //==========================================================================
        // Bug Fix:Ignore \000,Like String 'DOCUMENT' Encrypt And Decrypt
        // SHELL var_dump($txt) is showing: '\000' end with 'Document'
        // IDE var_dump($txt) is showing '&#0;' end with 'Document'
        //--------------------------------------------------------------------------
        $tmp = preg_replace('[\000]', '', $tmp);
        return $tmp;
    }
    
    
    static function StrEncrypt($txt)
    {
        $key = self::KEY;
        $chars = self::CHARS;
        $ikey = self::IKEY;
        $nh1 = rand(0,64);
        $nh2 = rand(0,64);
        $nh3 = rand(0,64);
        $ch1 = $chars[$nh1];
        $ch2 = $chars[$nh2];
        $ch3 = $chars[$nh3];
        $nhnum = $nh1 + $nh2 + $nh3;
        $knum = 0;$i = 0;
        while(isset($key[$i])) $knum +=ord($key[$i++]);
        $mdKey = substr(md5(md5(md5($key.$ch1).$ch2.$ikey).$ch3),$nhnum%8,$knum%8 + 16);
        $txt = base64_encode($txt);
        $txt = str_replace(array('+','/','='),array('-','_','.'),$txt);
        $tmp = '';
        $j=0;$k = 0;
        $tlen = strlen($txt);
        $klen = strlen($mdKey);
        for ($i=0; $i<$tlen; $i++) {
            $k = $k == $klen ? 0 : $k;
            $j = ($nhnum+strpos($chars,$txt[$i])+ord($mdKey[$k++]))%64;
            $tmp .= $chars[$j];
        }
        $tmplen = strlen($tmp);
        $tmp = substr_replace($tmp,$ch3,$nh2 % ++$tmplen,0);
        $tmp = substr_replace($tmp,$ch2,$nh1 % ++$tmplen,0);
        $tmp = substr_replace($tmp,$ch1,$knum % ++$tmplen,0);
        return $tmp;
    }
}

//custom function
function getFilenameFromConsole($arr)
{
    $len = count($arr);
    if(substr($arr[$len-1], 0, 1) !== '-') return $arr[$len-1];
    foreach ($arr as $val)
    {
        if (substr($val, 0, 1) !== '-') return $val;
    }
}

//help
if($argc==1 || in_array('-h', $argv)) {
    $help = <<<EOF
Desc: This is a file encrypt program
Usage:
    encryptfile [option] [filename]
    
    option:
        -e encrypt file [default]
        -d decrypt file
        -t test, output in console 
        -h help
    filename:
        required, file to be handle
EOF;
    echo $help, "\n\n";
    exit();
}


/**
* 程序处理
*/

$filename = getFilenameFromConsole($argv);
if (!file_exists($filename)) {
	echo "file is not exists, please check parame.";
	exit(1);
}

// echo mb_detect_encoding($filename); exit();
$content = file_get_contents($filename);

if(in_array('-d', $argv)) 
{
	$new_content = FileSafe::StrDecrypt($content);
} else {
	$new_content = FileSafe::StrEncrypt($content);
}

if(in_array('-t', $argv)) {
	echo $new_content;
	exit(1);
}

file_put_contents($filename, $new_content);

echo 'wonderful, successed!', "\n";
