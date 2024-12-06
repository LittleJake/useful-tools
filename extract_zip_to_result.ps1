# 解压所有zip文件（包括子目录）到result
function extract {
	param ($f)
	$name = $f.BaseName
	New-Item -ItemType Directory -Force -Path ".\result\$name" | Out-Null
	Expand-Archive -Path $f.FullName -D ".\result\$name" -Force
}


New-Item -ItemType Directory -Force -Path result | Out-Null
If($args.length -eq 1){
	Get-Item -Path $args[0] *.zip | ForEach-Object {extract($_)}
	Get-ChildItem -Path $args[0] -Dir | ? Name -notLike 'result' | Get-ChildItem -R -I *.zip | ForEach-Object {extract($_)}
}
Else
{
	Get-Item *.zip | ForEach-Object {extract($_)}
	Get-ChildItem -Dir | ? Name -notLike 'result' | Get-ChildItem -R -I *.zip | ForEach-Object {extract($_)}
}

Pause
