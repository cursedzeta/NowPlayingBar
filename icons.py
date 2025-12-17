# icons.py
# Iconitos dibujados con QPainter (minis de 16 px)

from PySide6 import QtGui, QtCore

def _mk_icon(paint_fn, w=16, h=16):
    pm = QtGui.QPixmap(w, h)
    pm.fill(QtCore.Qt.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.Antialiasing, True)
    paint_fn(p, w, h)
    p.end()
    return QtGui.QIcon(pm)

def icon_play():
    def paint(p, w, h):
        p.setBrush(QtGui.QColor("white")); p.setPen(QtCore.Qt.NoPen)
        pts = [QtCore.QPointF(w*0.30, h*0.20),
               QtCore.QPointF(w*0.30, h*0.80),
               QtCore.QPointF(w*0.78, h*0.50)]
        p.drawPolygon(QtGui.QPolygonF(pts))
    return _mk_icon(paint)

def icon_pause():
    def paint(p, w, h):
        p.setBrush(QtGui.QColor("white")); p.setPen(QtCore.Qt.NoPen)
        bw = w*0.22; gap = w*0.12
        p.drawRoundedRect(w*0.24, h*0.20, bw, h*0.60, 2, 2)
        p.drawRoundedRect(w*0.24+bw+gap, h*0.20, bw, h*0.60, 2, 2)
    return _mk_icon(paint)

def icon_next():
    def paint(p, w, h):
        p.setBrush(QtGui.QColor("white")); p.setPen(QtCore.Qt.NoPen)
        tri = [QtCore.QPointF(w*0.18, h*0.20),
               QtCore.QPointF(w*0.18, h*0.80),
               QtCore.QPointF(w*0.58, h*0.50)]
        p.drawPolygon(QtGui.QPolygonF(tri))
        p.drawRect(w*0.66, h*0.20, w*0.12, h*0.60)
    return _mk_icon(paint)

def icon_prev():
    def paint(p, w, h):
        p.setBrush(QtGui.QColor("white")); p.setPen(QtCore.Qt.NoPen)
        tri = [QtCore.QPointF(w*0.82, h*0.20),
               QtCore.QPointF(w*0.82, h*0.80),
               QtCore.QPointF(w*0.42, h*0.50)]
        p.drawPolygon(QtGui.QPolygonF(tri))
        p.drawRect(w*0.22, h*0.20, w*0.12, h*0.60)
    return _mk_icon(paint)

def icon_volume(level=100):
    """level: 0..100 → cambia levemente según volumen"""
    def paint(p, w, h):
        p.setBrush(QtGui.QColor("white")); p.setPen(QtCore.Qt.NoPen)
        # parlante
        p.drawRect(w*0.10, h*0.35, w*0.18, h*0.30)
        pts = [QtCore.QPointF(w*0.28, h*0.30),
               QtCore.QPointF(w*0.45, h*0.30),
               QtCore.QPointF(w*0.60, h*0.18),
               QtCore.QPointF(w*0.60, h*0.82),
               QtCore.QPointF(w*0.45, h*0.70),
               QtCore.QPointF(w*0.28, h*0.70)]
        p.drawPolygon(QtGui.QPolygonF(pts))
        # ondas
        pen = QtGui.QPen(QtGui.QColor("white")); pen.setWidthF(1.4); p.setPen(pen); p.setBrush(QtCore.Qt.NoBrush)
        if level > 0:
            p.drawArc(int(w*0.62), int(h*0.28), int(w*0.24), int(h*0.44), 60*16, -120*16)
        if level > 40:
            p.drawArc(int(w*0.70), int(h*0.20), int(w*0.32), int(h*0.60), 60*16, -120*16)
    return _mk_icon(paint)

def icon_mute():
    def paint(p, w, h):
        ic = icon_volume(0).pixmap(16,16)
        pm = QtGui.QPixmap(ic)
        painter = QtGui.QPainter(pm); painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QtGui.QPen(QtGui.QColor("red")); pen.setWidthF(2.0); painter.setPen(pen)
        painter.drawLine(w*0.60, h*0.28, w*0.88, h*0.72)
        painter.drawLine(w*0.88, h*0.28, w*0.60, h*0.72)
        painter.end()
        return QtGui.QIcon(pm)
    return icon_mute()

def icon_share():
    """Icono minimalista: flecha hacia arriba (outline)."""
    def paint(p, w, h):
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        pen = QtGui.QPen(QtGui.QColor("white"))
        pen.setWidthF(2.4)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)

        # ---- Triángulo superior (punta) ----
        tip = QtCore.QPointF(w * 0.50, h * 0.15)      # punta arriba
        left = QtCore.QPointF(w * 0.32, h * 0.40)     # base izquierda
        right = QtCore.QPointF(w * 0.68, h * 0.40)    # base derecha
        p.drawPolygon(QtGui.QPolygonF([tip, left, right]))

        # ---- Palo vertical de la flecha ----
        p.drawLine(
            QtCore.QPointF(w * 0.50, h * 0.40),
            QtCore.QPointF(w * 0.50, h * 0.80)
        )

    return _mk_icon(paint)
