if [[ -z "$1" ]]; then
	echo "Must pass in extern file to sandbox."
	exit 1
fi
EXTERN=$1
if [[ -z "$2" ]]; then 
	CONFIG_FILE="./ExtConfig.properties"
else
	CONFIG_FILE=$2
fi
if [[ ! -r "$CONFIG_FILE" ]]; then
	echo "Required config does not exist."
	exit 1	
fi
source "$CONFIG_FILE"
sed -i "s/Ext\./${ext_base}\./g" $EXTERN; sed -i "s/Ext /${ext_base} /g" $EXTERN