# Extjs Extern Generator

### Getting Started

1. Run jsduck on the required ext files in order to generate required json files
```
jsduck ext-all-debug.js packages/charts/classic/charts-debug.js other_files.js --export=full --output=/tmp/output_folder
```
2. Update ```ExtConfig.properties``` jsduck_location with ```/tmp/output_folder```
Run externGenerator and direct the output to a file
```
python externGenerator.py > myExtern.js
```
3. Sandbox Extjs (Optional)
Run externSandboxer and pass in ```myExtern.js```
```
sh externSandboxer.js myExtern.js
```

### Closure Compiler (with Extjs compiling)

<table>
  <tr>
    <td>URL</td>
    <td><a href="https://github.com/TMCBonds/closure-compiler">https://github.com/TMCBonds/closure-compiler</a></td>
  </tr>
  <tr>
    <td>Description</td>
    <td>JS compilation library with additional processing for Extjs</td>
  </tr>
</table>

### Extjs Closure Compiler Externs

<table>
  <tr>
    <td>URL</td>
    <td><a href="https://github.com/TMCBonds/ext-externs">https://github.com/TMCBonds/ext-externs</a></td>
  </tr>
  <tr>
    <td>Description</td>
    <td>Extjs extern for Closure Compiler</td>
  </tr>
</table>
