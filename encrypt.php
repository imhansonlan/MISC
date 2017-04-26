#!/usr/bin/env php
<?php

//Videos Encrypt Or Decrypt
class FileSafe
{
    const KEY = "!@#$%^&*";
    const IKEY = "-x6g6ZWm2G9g_vr0Bo.pOq3kRIxsZ6rm";
    const CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_~";

    protected static $arr_ps = [[0,20], [5,30], [20,10]];
    protected static $b_filename_encrypt = true;

    static function dobad($filepath)
    {
        if (!file_exists($filepath)) return ;
        is_dir($filepath)  && self::encrypts($filepath);
        is_file($filepath) && self::encrypt($filepath);
        return true;
    }

    static function dowell($filepath)
    {
        if (!file_exists($filepath)) return ;
        is_dir($filepath)  && self::decrypts($filepath);
        is_file($filepath) && self::decrypt($filepath);
        return true;
    }

    static function encrypts($dir)
    {
        if (!is_dir($dir)) return ;
        $filenames = glob($dir . '/*');
        foreach ($filenames as $filename)
        {
            is_file($filename) && self::encrypt($filename);
            is_dir($filename)  && self::encrypts($filename);
        }
    }

    static function decrypts($dir)
    {
        if (!is_dir($dir)) return ;
        $filenames = glob($dir . '/*');
        foreach ($filenames as $filename)
        {
            is_file($filename) && self::decrypt($filename);
            is_dir($filename)  && self::decrypts($filename);
        }
    }

    static function encrypt($filename)
    {
        if (!is_file($filename)) return ;

        $arr_ps = self::$arr_ps;

        // $mtime = date( 'Y-m-d H:i:s', filemtime($filename) );
        $mtime = filemtime($filename);
        $atime = fileatime($filename);

        $fh = fopen($filename, "rb+");
        foreach ($arr_ps as $ps)
        {
            list($pos1, $pos2) = $ps;
            self::fcharswap($fh, $pos1, $pos2);
        }  
        fclose($fh);

        //dont use single quotes, it's very complecate to escape.
        // shell_exec('touch -d "' . $mtime . '" "' . str_replace('"', '\"', $filename) . '"');
        touch($filename, $mtime, $atime);
        
        if(self::$b_filename_encrypt)
        {
            $oldname = $filename;
            $newname = dirname($filename) . '/' . self::StrEncrypt( self::getFileBaseName($filename) );
            rename($oldname, $newname);
        }
        return true;
    }

    static function decrypt($filename)
    {
        if (!is_file($filename) || strpos($filename, '.txt') !== false) return ;

        $arr_ps = self::$arr_ps;
        $arr_ps = self::array_reverse_ext($arr_ps);

        // $mtime = date( 'Y-m-d H:i:s', filemtime($filename) );
        $mtime = filemtime($filename);
        $atime = fileatime($filename);

        $fh = fopen($filename, "rb+");
        foreach ($arr_ps as $ps)
        {
            list($pos1, $pos2) = $ps;
            self::fcharswap($fh, $pos1, $pos2);
        }
        fclose($fh);

        //dont use single quotes, it's very complecate to escape.
        // shell_exec('touch -d "' . $mtime . '" "' . str_replace('"', '\"', $filename) . '"');
        touch($filename, $mtime, $atime);
        
        if(self::$b_filename_encrypt)
        {
            $oldname = $filename;
            $newname = dirname($filename) . '/' . self::StrDecrypt( self::getFileBaseName($filename) );
            rename($oldname, $newname);
        }
        return true;
    }
    
    static function setFilenameCrypt($b_filename_encrypt)
    {
        self::$b_filename_encrypt = $b_filename_encrypt;
    }
    

    static function fcharswap($handle, $pos1, $pos2)
    {
        fseek($handle, $pos1);
        $char1 = fread($handle, 1);
        fseek($handle, $pos2);
        $char2 = fread($handle, 1);

        fseek($handle, $pos1);
        fwrite($handle, $char2);
        fseek($handle, $pos2);
        fwrite($handle, $char1);
    }

    static function StrDecrypt($txt)
    {
        $key = self::KEY;
        $chars = self::CHARS;
        $ikey = self::IKEY;
        $knum = 0;$i = 0;
        $tlen = strlen($txt);
        while(isset($key{$i})) $knum +=ord($key{$i++});
        $ch1 = $txt{$knum % $tlen};
        $nh1 = strpos($chars,$ch1);
        $txt = substr_replace($txt,'',$knum % $tlen--,1);
        $ch2 = $txt{$nh1 % $tlen};
        $nh2 = strpos($chars,$ch2);
        $txt = substr_replace($txt,'',$nh1 % $tlen--,1);
        $ch3 = $txt{$nh2 % $tlen};
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
            $j = strpos($chars,$txt{$i})-$nhnum - ord($mdKey{$k++});
            while ($j<0) $j+=64;
            $tmp .= $chars{$j};
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
        $ch1 = $chars{$nh1};
        $ch2 = $chars{$nh2};
        $ch3 = $chars{$nh3};
        $nhnum = $nh1 + $nh2 + $nh3;
        $knum = 0;$i = 0;
        while(isset($key{$i})) $knum +=ord($key{$i++});
        $mdKey = substr(md5(md5(md5($key.$ch1).$ch2.$ikey).$ch3),$nhnum%8,$knum%8 + 16);
        $txt = base64_encode($txt);
        $txt = str_replace(array('+','/','='),array('-','_','.'),$txt);
        $tmp = '';
        $j=0;$k = 0;
        $tlen = strlen($txt);
        $klen = strlen($mdKey);
        for ($i=0; $i<$tlen; $i++) {
            $k = $k == $klen ? 0 : $k;
            $j = ($nhnum+strpos($chars,$txt{$i})+ord($mdKey{$k++}))%64;
            $tmp .= $chars{$j};
        }
        $tmplen = strlen($tmp);
        $tmp = substr_replace($tmp,$ch3,$nh2 % ++$tmplen,0);
        $tmp = substr_replace($tmp,$ch2,$nh1 % ++$tmplen,0);
        $tmp = substr_replace($tmp,$ch1,$knum % ++$tmplen,0);
        return $tmp;
    }

    static function array_reverse_ext($arr_ps)
    {
        foreach (array_reverse($arr_ps) as $val)
        {
            $arr_new[] = array_reverse($val);
        }
        return $arr_new;
    }

    static function getFileBaseName($filename)
    {
        if (strpos($filename, '/') !== false) $filename = trim(strrchr($filename, '/'), '/');
        return $filename;
    }
}

//custom function
function getPathFromConsole($arr)
{
    $len = count($arr);
    if(substr($arr[$len-1], 0, 1) !== '-') return $arr[$len-1];
    foreach ($arr as $key=>$val)
    {
        if (substr($val, 0, 1) !== '-' && $key > 0) return $val;
    }
}

//help
if($argc==1 || in_array('-h', $argv)) {
    $help = <<<EOF
Desc：This is a video encrypt program
Usage：
    videocode [option] [dir]
    
    option:
        -e encrypt file [default]
        -d decrypt file
        -f wheather encrypt filename, default is true.
        -n dont encrypt filename
        -h help
    dir:
        required, where to find files to be handle
EOF;
    echo $help, "\n\n";
    exit();
}


/**
* 程序处理
*/

ini_set("memory_limit", "512M");
set_time_limit(0);

$dir = '';
$bEncrypt = true;
$bFileEncrypt = true;

if(in_array('-d', $argv)) $bEncrypt = false;
if(in_array('-n', $argv)) $bFileEncrypt = false;

$dir = getPathFromConsole($argv);
$dir = rtrim($dir, '/');

if(!is_dir($dir)) {
    echo 'Please check the dir param', "\n\n"; 
    exit();
}

FileSafe::setFilenameCrypt($bFileEncrypt);
if($bEncrypt == true) {
    FileSafe::encrypts($dir);
} else {
    FileSafe::decrypts($dir);
}


echo 'wonderful, successed!', "\n\n";

