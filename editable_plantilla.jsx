// Crea Demo_Factoring_Editable.prproj: keyframes, titulos y efectos nativos de Premiere.
// armar_editable.py completa los datos y genera crear_editable.jsx. Se ejecuta con Premiere CERRADO.
(function () {
  var D = /*DATOS*/null;
  var dir = new File($.fileName).parent.fsName + "\\";
  var log = new File(dir + "crear_editable.log"); log.encoding = "UTF-8"; log.open("w"); log.close();
  function L(s) { log.open("a"); log.writeln(s); log.close(); }
  function T(n, f) { try { var r = f(); if (r !== undefined) L("[" + n + "] " + r); } catch (e) { L("[" + n + "] ERROR " + e + " linea " + e.line); } }
  var TICKS = 254016000000, BEZIER = 5, LINEAL = 0;
  function modo(m) { return m === "lineal" ? LINEAL : BEZIER; }
  function tm(seg) { var t = new Time(); t.seconds = seg; return t; }

  function claves(p, lista) {                     // lista: [[seg, valor, modo], ...]
    p.setTimeVarying(true);
    for (var i = 0; i < lista.length; i++) { p.addKey(lista[i][0]); p.setValueAtKey(lista[i][0], lista[i][1], true); }
    for (var j = 0; j < lista.length; j++) p.setInterpolationTypeAtKey(lista[j][0], modo(lista[j][2]), true);
  }

  var prj = dir + "Demo_Factoring_Editable.prproj";
  if (new File(prj).exists) { L("YA EXISTE"); L("FIN"); return; }
  T("nuevo", function () { return app.newProject(prj); });
  T("xml", function () { return app.project.importFiles([dir + "Demo_Factoring_Editable.xml"], true, app.project.rootItem, false); });
  app.project.openSequence(app.project.sequences[0].sequenceID);
  var seq = app.project.activeSequence;
  T("pistas", function () { return seq.videoTracks.numTracks + " video, " + seq.audioTracks.numTracks + " audio, v1=" + seq.videoTracks[0].clips.numItems + " v2=" + seq.videoTracks[1].clips.numItems; });

  // Camara: zoom y paneo como keyframes de Movimiento en V1
  var v1 = seq.videoTracks[0];
  for (var i = 0; i < D.clips.length; i++) (function (c) {
    T("cam " + c.nombre, function () {
      var clip = v1.clips[c.indice], mo = clip.components[1], pos = mo.properties[0], esc = mo.properties[1], k = c.claves;
      if (k.length === 1) { esc.setValue(k[0][1], true); pos.setValue([k[0][2], k[0][3]], true); return; }
      var e = [], p = [];
      for (var j = 0; j < k.length; j++) { e.push([k[j][0], k[j][1], k[j][4]]); p.push([k[j][0], [k[j][2], k[j][3]], k[j][4]]); }
      claves(esc, e); claves(pos, p);
    });
  })(D.clips[i]);

  // Grabaciones sin camara y fondos: la 4K entra a 50 %
  T("escala fondos", function () {
    var n = 0;
    for (var i = 0; i < v1.clips.numItems; i++) { var c = v1.clips[i], e = c.components[1].properties[1]; if (!e.isTimeVarying()) { if (c.name.indexOf("fondo") === 0) e.setValue(D.escala_base, true); n++; } }
    return n + " clips sin keyframes";
  });

  // Ventana flotante: escala, opacidad y sombra en V2
  app.enableQE();
  var q = qe.project.getActiveSequence(), v2 = seq.videoTracks[1], sombra = null;   // la sombra por script falla: la guia explica como agregarla a mano
  for (var w = 0; w < D.ventanas.length; w++) (function (vn, idx) {
    T("ventana " + vn.nombre, function () {
      var clip = v2.clips[idx], mo = clip.components[1], esc = mo.properties[1], op = clip.components[0].properties[0];
      claves(esc, vn.claves);
      var a = vn["in"], b = a + vn.dur, f = 6 / D.fps;
      claves(op, [[a, 0, "bezier"], [a + f, 100, "bezier"], [b - f, 100, "bezier"], [b, 0, "bezier"]]);
      if (sombra) {
        // QE cuenta los huecos de la pista como elementos: se busca el clip por nombre
        var pq = q.getVideoTrackAt(1), it = null;
        for (var h = 0; h < pq.numItems; h++) { var cand = pq.getItemAt(h); if (cand.name === vn.nombre) it = cand; }
        if (!it) return "clip no hallado en QE";
        it.addVideoEffect(sombra);
        $.sleep(400);
        var fresco = seq.videoTracks[1].clips[idx], s = null;
        for (var n = 0; n < fresco.components.numItems; n++) if (fresco.components[n].displayName === "Sombra paralela") s = fresco.components[n];
        if (!s) return "sin sombra";
        s.properties[1].setValue(115, true); s.properties[2].setValue(180, true); s.properties[3].setValue(22, true); s.properties[4].setValue(80, true);
      }
    });
  })(D.ventanas[w], w);

  // Logo del cierre
  T("logo", function () {
    var c = v2.clips[D.ventanas.length], op = c.components[0].properties[0], a = c.inPoint.seconds;
    c.components[1].properties[0].setValue([.5, .56], true);
    claves(op, [[a, 0, "bezier"], [a + .5, 100, "bezier"]]);
  });

  // Titulos: Basic Title. El texto definitivo lo escribe parchar_textos.py (la API no puede escribirlo bien);
  // aqui se deja un marcador unico en cada uno.
  var mogrt = Folder.userData.fsName + "/Adobe/Common/Motion Graphics Templates/Basic Title.mogrt";
  var usados = {};
  for (var x = 0; x < D.textos.length; x++) (function (t) {
    T("texto " + t.id, function () {
      var clave = t.ini, pista = usados[clave] ? 4 : 3; usados[clave] = 1;
      var ini = t.ini + t.ent, dur = t.dur - t.ent, c = seq.importMGT(mogrt, String(Math.round(ini * 30) * TICKS / 30), pista, 2);
      c.end = tm(ini + dur);
      var op = c.components[0].properties[0], mo = c.components[1], tx = c.components[3];
      tx.properties[0].setValue(t.id, true);
      tx.properties[2].setValue([.5, t.y], true);
      tx.properties[3].setValue(t.tam, true);               // Escala del texto: el tamano real se ajusta aqui
      var a = c.inPoint.seconds, b = c.outPoint.seconds, f = 6 / D.fps;
      if (t.tipo === "tecleo") {
        var der = mo.properties[9];
        claves(der, [[a, 85, "lineal"], [a + 1.45, 12, "lineal"]]);
        claves(op, [[a, 100, "lineal"], [b - f, 100, "bezier"], [b, 0, "bezier"]]);
      } else {
        var esc = mo.properties[1], pos = mo.properties[0], e = t.tipo === "golpe" ? .4 : .45;
        if (t.tipo === "golpe") claves(esc, [[a, 90, "bezier"], [a + e, 100, "bezier"]]);
        else claves(pos, [[a, [.5, .528], "bezier"], [a + e, [.5, .5], "bezier"]]);
        claves(op, [[a, 0, "bezier"], [a + e * .7, 100, "bezier"], [b - f, 100, "bezier"], [b, 0, "bezier"]]);
      }
    });
  })(D.textos[x]);

  T("control suavizado", function () {
    var c = D.clips[0], clip = v1.clips[c.indice], esc = clip.components[1].properties[1], k = c.claves;
    if (k.length < 2) return "sin claves";
    var a = k[k.length - 2], b = k[k.length - 1], o = [];
    for (var f = 0; f <= 4; f++) { var u = a[0] + (b[0] - a[0]) * f / 4; o.push(Math.round(esc.getValueAtTime(u) * 100) / 100); }
    return c.nombre + " de " + a[1] + " a " + b[1] + ": " + o.join(", ");
  });
  T("guardar", function () { return app.project.save(); });
  L("FIN");
  app.quit();
})();
