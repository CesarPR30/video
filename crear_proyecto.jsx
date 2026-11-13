// Crea Demo_Factoring_60s.prproj e importa la secuencia. Lo ejecuta Premiere al abrir:
//   "Adobe Premiere Pro.exe" /C es.processFile "ruta\crear_proyecto.jsx"
// Escribe el resultado en crear_proyecto.log para poder verificarlo.
(function () {
  var dir = new File($.fileName).parent.fsName + "\\";
  var log = new File(dir + "crear_proyecto.log");
  log.encoding = "UTF-8"; log.open("w");
  try {
    var prproj = dir + "Demo_Factoring_60s.prproj";
    if (new File(prproj).exists) { log.writeln("YA EXISTE: no se sobrescribe"); log.close(); return; }
    log.writeln("newProject: " + app.newProject(prproj));
    log.writeln("importFiles: " + app.project.importFiles([dir + "Demo_Factoring_60s.xml"], true, app.project.rootItem, false));
    log.writeln("secuencias: " + app.project.sequences.numSequences);
    app.project.save();
    log.writeln("guardado: " + app.project.path);
  } catch (e) { log.writeln("ERROR: " + e); }
  log.close();
})();
