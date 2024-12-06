# 压缩文件夹下的所有文件夹为zip压缩包
function compress {
	param ($f, [string]$d)
	$name = $f.BaseName
	Compress-Archive -Path $f.FullName -DestinationPath "$d$name" -Force
}

If($args.length -eq 1){
	Get-ChildItem -Path $args[0] -Dir | ForEach-Object {compress $_ $args[0]}
}
Else{
	Get-ChildItem -Dir | ForEach-Object {compress $_ ".\" }
}
Pause
