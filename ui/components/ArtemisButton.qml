import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material


Button {
    id: control

    property string type: "primary"
    property bool visibleBackground: false
    property string hoverAlphaHex: "1A"

    flat: true
    hoverEnabled: true

    function getColor(type) {
        const colors = {
            "success": control.Material.color(control.Material.Green),
            "warning": control.Material.color(control.Material.Orange),
            "danger":  control.Material.color(control.Material.Red),
            "primary": control.parent ? control.parent.Material.accent : control.Material.accent
        };
        
        return colors[type] || (control.parent ? control.parent.Material.accent : control.Material.accent);
    }

    Material.foreground: control.hovered
        ? control.getColor(control.type)
        : control.parent.Material.foreground

    Material.background: (control.visibleBackground || control.hovered)
        ? ("#" + control.hoverAlphaHex + control.getColor(control.type).toString().substring(1))
        : "transparent"
}
