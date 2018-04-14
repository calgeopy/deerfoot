import sys
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui

from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog,QListWidgetItem,QMessageBox,QLabel)
from PyQt5.uic import loadUi

from welly import Well

#w = None


class AppMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi("calgeopy_march27.ui", self)

        self.actionAbout.triggered.connect(self.clickAbout)

        self.btnGetfilename.clicked.connect(self.getfilename)
        self.btn_loadlas.clicked.connect(self.loadlas)
        self.btnPlotlas.clicked.connect(self.plotlas)

        self.btn_addtop.clicked.connect(self.addtop)
        self.btn_plottops.clicked.connect(self.plottops)

        self.btn_startcrossplot.clicked.connect(self.startcrossplot)
        self.btn_trendline.clicked.connect(self.plottrendline)


        self.tops=[]


    def addtop(self):
        topname=self.le_topname.text()
        topdepth=float(self.le_topdepth.text())
        self.tops.append([topname,topdepth])

        text = self.tops[-1][0]+','+str(self.tops[-1][1])
        item = QListWidgetItem(text)
        #item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        #item.setCheckState(QtCore.Qt.Checked)
        self.tbl_tops.addItem(item)
        self.tbl_tops.update()

    def plottops(self):

        for tp in self.tops:
            self.gvPlot1.addLine(x=None, y=tp[1])
            tp_txt=pg.TextItem(text=tp[0])
            self.gvPlot1.addItem(tp_txt)
            tp_txt.setPos(15,tp[1],)
            self.gvPlot2.addLine(x=None, y=tp[1])
            self.gvPlot3.addLine(x=None, y=tp[1])
            self.gvPlot4.addLine(x=None, y=tp[1])




    def getfilename(self):
        dir = sys.path[-1]
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            dir, "LAS file (*.las)")
        self.le_filename.setText(str(fname[0].replace('\\', '/')))

        self.cb_plot1.clear()
        self.cb_plot2.clear()
        self.cb_plot3.clear()
        self.cb_plot4.clear()
        self.cb_x.clear()
        self.cb_y.clear()
        self.cb_points.clear()

        self.gvPlot1.clear()
        self.gvPlot2.clear()
        self.gvPlot3.clear()
        self.gvPlot4.clear()


    def loadlas(self):
        filename = self.le_filename.text()

        self.w = Well.from_las(filename)

        curves =self.w.df().columns
        #print(curves)

        for c in curves:
            self.cb_plot1.addItem(c)
            self.cb_plot2.addItem(c)
            self.cb_plot3.addItem(c)
            self.cb_plot4.addItem(c)
            self.cb_x.addItem(c)
            self.cb_y.addItem(c)
            self.cb_points.addItem(c)







    def plotlas(self):

        y = self.w.survey_basis()

        x = self.w.data[self.w.df().columns[self.cb_plot1.currentIndex()]]
        self.gvPlot1.clear()
        self.gvPlot1.plot(x,y,pen=(1, 4))
        self.gvPlot1.invertY(True)
        self.gvPlot1.setTitle(self.w.df().columns[self.cb_plot1.currentIndex()])
        self.gvPlot1.setMouseEnabled(x=False, y=True)

        x =self.w.data[self.w.df().columns[self.cb_plot2.currentIndex()]]
        self.gvPlot2.clear()
        self.gvPlot2.plot(x, y,pen=(2, 4))
        self.gvPlot2.invertY(True)
        self.gvPlot2.setTitle(self.w.df().columns[self.cb_plot2.currentIndex()])
        self.gvPlot2.setYLink(self.gvPlot1)
        self.gvPlot2.setMouseEnabled(x=False, y=True)

        x =self.w.data[self.w.df().columns[self.cb_plot3.currentIndex()]]
        self.gvPlot3.clear()
        self.gvPlot3.plot(x, y,pen=(3, 4))
        self.gvPlot3.invertY(True)
        self.gvPlot3.setTitle(self.w.df().columns[self.cb_plot3.currentIndex()])
        self.gvPlot3.setYLink(self.gvPlot1)
        self.gvPlot3.setMouseEnabled(x=False, y=True)

        x =self.w.data[self.w.df().columns[self.cb_plot4.currentIndex()]]
        self.gvPlot4.clear()
        self.gvPlot4.plot(x, y,pen=(4, 4))
        self.gvPlot4.invertY(True)
        self.gvPlot4.setTitle(self.w.df().columns[self.cb_plot4.currentIndex()])
        self.gvPlot4.setYLink(self.gvPlot1)
        self.gvPlot4.setMouseEnabled(x=False, y=True)


    def startcrossplot(self):
        import matplotlib
        from matplotlib import cm

        x = self.w.data[self.w.df().columns[self.cb_x.currentIndex()]]
        y = self.w.data[self.w.df().columns[self.cb_y.currentIndex()]]
        color = self.w.data[self.w.df().columns[self.cb_points.currentIndex()]]


        clrs = color/max(color)          # scale color for cmap, needs to be 0to1
        clrs = [x if x<1 else 1 for x in clrs]

        cmap = matplotlib.cm.get_cmap('terrain')     #sets cmap to terrain, can be any matplotlib colormap
        c1=cmap(clrs, bytes=True )  # calls rbg from cmap

        self.scatter.clear()
        data1 = self.scatter.plot()
        data1.setData(x,y,pen=None,symbol='o', symbolPen=None, symbolSize=5,symbolBrush=[pg.mkBrush(c) for c in c1],pxMode=True )
        self.scatter.setLabel('bottom',self.w.df().columns[self.cb_x.currentIndex()])
        self.scatter.setLabel('left',self.w.df().columns[self.cb_y.currentIndex()])



    def plottrendline(self):
        x = np.array(self.w.data[self.w.df().columns[self.cb_x.currentIndex()]])
        y = np.array(self.w.data[self.w.df().columns[self.cb_y.currentIndex()]])

        idx = np.isfinite(x) & np.isfinite(y)
        fit = np.polyfit(x[idx], y[idx], 1)
        slope,intercept = fit
        self.le_trendlineslope.setText(str(slope))
        self.le_trendlineint.setText(str(intercept))
        xfit=[min(x[idx]),max(x[idx])]
        yfit = [slope*xx + intercept for xx in xfit]
        self.scatter.plot(xfit, yfit, pen='r')



    def clickAbout(self):
        QMessageBox.about(self, "About", "Created by calgeopy\nMarch, 2018")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWnd = AppMainWindow()

    # Attach the File->Exit menu item to the slot to close the window
    mainWnd.actionExit.triggered.connect(mainWnd.close)

    # Show the window
    mainWnd.show()

    # Start the main messageloop
    sys.exit(app.exec_())