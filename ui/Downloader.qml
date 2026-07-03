import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Controls.Material
import QtQuick.Layouts

import './components' as UIComponents


Window {
    id: windowDownloader

    width: 400
    height: 130

    maximumHeight: height
    maximumWidth: width

    minimumHeight: height
    minimumWidth: width

    modality: Qt.ApplicationModal
    flags: Qt.Dialog

    title: qsTr("Artemis - Downloader")

    signal abortRequested()

    onClosing: {
        abortRequested()
    }

    function updateProgressBar(bytesReceived, bytesTotal) {
        progressBar.indeterminate = false
        progressBar.value = bytesReceived
        progressBar.to = bytesTotal
    }

    function setIndeterminateBar() {
        progressBar.indeterminate = true
    }

    function updateStatus(arg) {
        progressLabel.text = arg
    }

    Page {
        id: page
        anchors.fill: parent

        ColumnLayout {
            id: columnLayout
            anchors.fill: parent
            anchors.margins: 10

            Label {
                text: qsTr("Download in progress...")
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            }

            ProgressBar {
                id: progressBar
                Layout.rightMargin: 20
                Layout.leftMargin: 20
                Layout.fillWidth: true
                indeterminate: false
                value: 0
                to: 0
            }

            Label {
                id: progressLabel
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
            }

            UIComponents.ArtemisButton {
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom
                text: qsTr("Cancel")
                icon.source: "qrc:/data/images/icons/cancel.svg"
                type: "danger"
                display: AbstractButton.TextBesideIcon
                onClicked: { abortRequested() }
            }
        }
    }
}
