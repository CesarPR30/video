// Abre el proyecto editable, cuenta lo que Premiere cargo y exporta cuadros de control.
(function () {
  var dir = new File($.fileName).parent.fsName + "\\";
  var sal = dir + "verificacion\\";
  var log = new File(dir + "verificar.log"); log.encoding = "UTF-8"; log.open("w"); log.close();
  function L(s) { log.open("a"); log.writeln(s); log.close(); }
  function T(n, f) { try { var r = f(); if (r !== undefined) L("[" + n + "] " + r); } catch (e) { L("[" + n + "] ERROR " + e + " linea " + e.line); } }
  T("abrir", function () { return app.openDocument(dir + "Demo_Factoring_Editable.prproj", true, true, true); });
  app.project.openSequence(app.project.sequences[0].sequenceID);
  var seq = app.project.activeSequence;
  T("secuencia", function () { return seq.name + " " + seq.end / 254016000000 + " s"; });
  T("pistas", function () {
    var o = [];
    for (var i = 0; i < seq.videoTracks.numTracks; i++) o.push("V" + (i + 1) + "=" + seq.videoTracks[i].clips.numItems + "c/" + seq.videoTracks[i].transitions.numItems + "t");
    for (var a = 0; a < seq.audioTracks.numTracks; a++) o.push("A" + (a + 1) + "=" + seq.audioTracks[a].clips.numItems + "c");
    return o.join(" ");
  });
  T("keyframes", function () {
    var n = 0, t = seq.videoTracks[0];
    for (var i = 0; i < t.clips.numItems; i++) { var e = t.clips[i].components[1].properties[1]; if (e.isTimeVarying()) n += e.getKeys().length; }
    return n + " claves de escala en V1";
  });
  T("curva", function () {
    var c = seq.videoTracks[0].clips[4], e = c.components[1].properties[1], k = e.getKeys(), a = k[k.length - 2].seconds, b = k[k.length - 1].seconds, o = [];
    for (var f = 0; f <= 8; f++) o.push(Math.round(e.getValueAtTime(a + (b - a) * f / 8) * 100) / 100);
    return c.name + ": " + o.join(", ");
  });
  T("sombra", function () {
    var c = seq.videoTracks[1].clips[0], s = c.components[c.components.numItems - 1], o = [];
    for (var i = 1; i <= 4; i++) o.push(s.properties[i].displayName + "=" + s.properties[i].getValue());
    return s.displayName + " " + o.join(", ");
  });
  T("textos", function () {
    var o = [];
    for (var v = 3; v <= 4; v++) { var t = seq.videoTracks[v]; for (var i = 0; i < t.clips.numItems; i++) o.push(Math.round(t.clips[i].start.seconds * 10) / 10); }
    return o.length + " en s: " + o.join(", ");
  });
  app.enableQE();
  var q = qe.project.getActiveSequence();
  var seg = [1.9, 4.9, 6.6, 8.4, 9.5, 11, 14, 17, 19, 20.6, 23.5, 26.5, 29, 31.5, 33, 35.3, 38.5, 41, 42.5, 44.5, 48, 50.2, 53, 56.8, 58.8];
  for (var i = 0; i < seg.length; i++) (function (s, i) {
    T("png", function () {
      L("cuadro " + s);
      seq.setPlayerPosition(String(Math.round(s * 30) * 8467200000));
      $.sleep(700);
      var nom = ("0" + i).slice(-2) + "_" + String(s).replace(".", "s") + ".png";
      q.exportFramePNG(q.CTI.timecode, sal + nom);
      return undefined;
    });
  })(seg[i], i);
  seq.setPlayerPosition("0");
  $.sleep(4000);
  L("FIN");
})();
