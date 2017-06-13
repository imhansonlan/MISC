#!/bin/bash
# vim: fdm=marker ts=2 sw=2 sts=2 expandtab

__ScriptVersion="1.0.0"
__ScriptName=$(basename "$0")
__ScriptRoot=$(dirname "$0")

#===  FUNCTION  ================================================================
#         NAME:  usage
#  DESCRIPTION:  Display usage information.
#===============================================================================
function usage ()
{
  echo "Usage :  $__ScriptName [options] file/dir

  Options:
  -d|decode     action as decode file
  -e|encode     action as encode file
  -j|jobs       Default: 50. Number of jobslots. Run up to N jobs in parallel
  -h|help       Display this message
  -v|version    Display script version"

}    # ----------  end of function usage  ----------


#-----------------------------------------------------------------------
#  Depands check
#-----------------------------------------------------------------------
if ! which parallel &>/dev/null; then
  echo 'need parallel command, you can install like "apt install parallel" in Ubuntu.'
  exit 
fi

#-----------------------------------------------------------------------
#  Handle command line arguments
#-----------------------------------------------------------------------
[[ -z "$1" ]] && usage && exit 1

# variables
declare file action jobs works

# parse short params
while getopts ":f:dej:w:hv" opt
do
  case $opt in

    d|decode   )  action='decode'   ;;

    e|encode   )  action='encode'   ;;

    j|jobs     )  jobs=$OPTARG      ;;

    h|help     )  usage; exit 0     ;;

    v|version  )  echo "$__ScriptName -- Version $__ScriptVersion"; exit 0   ;;

  esac    # --- end of case ---
done
shift $(($OPTIND-1))

#-----------------------------------------------------------------------
#  Main codes
#-----------------------------------------------------------------------
path=$(echo "$*" | grep -P -o '(?!-[a-zA-Z]).+(?!-[a-zA-Z])$')

[[ -z "$action" ]] && action="encode"
[[ -z "$jobs" ]] && jobs=50

[[ "$action" == "encode" ]] && action='-e' || action='-d'

# check path
if [[ ! -e "$path" ]]; then
  echo -e "\n\x1b[38;5;1mFile not exist : $path \x1b[0m \n"
  usage; exit 1
fi

# do action
stime=$SECONDS
find "$path" -type f | parallel --no-notice -j $jobs $__ScriptRoot/encrypt.php -q $action
etime=$SECONDS
printf "release time: %d Seconds\n" $(($etime - $stime))

