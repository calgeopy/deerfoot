import sys
import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pandas as pd
import bruges
import lasio
from welly import Well
import lxml


from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog,QListWidgetItem,QTableWidgetItem,
                             QMessageBox,QLabel)
from PyQt5.uic import loadUi


curves_info = lxml.etree.parse('CurveData.xml').getroot()

#curve_displ=[{'name': 'Son-Den','curves':['GR','DT','RHOB']}];
#curve_displ.append({'name': 'Res','curves':['GR','RLA5','RLA4','RLA3']});
#curve_displ.append({'name': 'Son-Shear','curves':['GR','DT','DTS']});
#curve_displ.append({'name': 'Porosity-Lime','curves':['GR','DPHI_LIM','NPHI_LIM']});

curve_displ=[{'name': 'Son-Den','curves':['GammaRay','Sonic','Density']}];
curve_displ.append({'name': 'Res','curves':[['GammaRay','SelfPot'],['DeepRes','MedRes','ShallowRes']]});
curve_displ.append({'name': 'Son-Shear','curves':['GammaRay','Sonic','ShearSonic']});
curve_displ.append({'name': 'Porosity-Lime','curves':['GammaRay',['DenPorLime','NeutPorLime']]});
curve_displ.append({'name': 'Porosity-Sand','curves':['GammaRay',['DenPorSand','NeutPorSand']]});
curve_displ.append({'name': 'Porosity-Dol','curves':['GammaRay',['DenPorDol','NeutPorDol']]});
curve_displ.append({'name': 'LMR','curves':[['GammaRay','SelfPot'],'Lambda','Mu','Density']});

class AppMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi("deerfoot_new.ui", self)

        self.actionAbout.triggered.connect(self.clickabout)
#        self.actionSetup.triggered.connect(self.menusetup)

#        self.btnGetfilename.clicked.connect(self.getfilename)
        self.btn_loadlas.clicked.connect(self.loadlas)
#        self.btnPlotlas.clicked.connect(self.plotlasOLD)
        self.btnPlotlas.clicked.connect(self.plotlas)
        

        self.btn_addtop.clicked.connect(self.addtop)
        self.btn_plottops.clicked.connect(self.plottops)
        self.btn_removetop.clicked.connect(self.removetop)

#added by C. Hooge    
        self.btn_loadtops.clicked.connect(self.loadtops)

        self.btn_startcrossplot.clicked.connect(self.startcrossplot)
        self.btn_trendline.clicked.connect(self.plottrendline)

        self.tops = []
        self.plots = []
        self.crossplotisdispayed = False
        
#        self.hzSlider_slope.valueChanged.connect(self.Slidervaluechange)

    def removetop(self):
        remtop = self.tbl_tops.currentRow()
        self.tops.remove(self.tops[remtop])

        # item = self.tbl_tops.takeItem(remtop)
        # item = None

        self.plotlas()
        self.plottops()

    def addtop(self):
        topname = self.le_topname.text()
        topdepth = float(self.le_topdepth.text())
        self.tops.append([topname, topdepth])

#        text = self.tops[-1][0]+','+str(self.tops[-1][1])
#        item = QListWidgetItem(text)
        # item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        # item.setCheckState(QtCore.Qt.Checked)
#        self.tbl_tops.addItem(item)
#        self.tbl_tops.update()
        
        rowPosition = self.tbl_tops.rowCount()
        self.tbl_tops.insertRow(rowPosition)
        self.tbl_tops.setItem(rowPosition , 0, QTableWidgetItem(self.tops[-1][0]))
        self.tbl_tops.setItem(rowPosition , 1, QTableWidgetItem(str(self.tops[-1][1])))
        
#added by C. Hooge    
    def loadtops(self):
        path = sys.path[-1]
        tp = QFileDialog.getOpenFileName(self, 'Open file',
                                            path, "Tops file (*.csv *.xlsx)")
        topsfile = tp[0].replace('\\', '/')
#        self.tp_filename.setText(str(topsfile[0].replace('\\', '/')))
#        print('here',topsfile.endswith('.csv'))

        if (topsfile.endswith('.xlsx')):
            topdata=pd.read_excel(topsfile, index_col=0);
        if (topsfile.endswith('.csv')):
            topdata=pd.read_csv(topsfile, index_col=0);
#        uwi = self.w.las.header['Well']['UWI'].value;
        well_tops=topdata[(topdata.index == self.w.las.header['Well']['UWI'].value)]
        well_tops = well_tops.drop(['KB'], axis=1).squeeze().to_dict()
        
        for key, value in well_tops.items():
#            print('t',key,value)
            self.tops.append([key, value])

            rowPosition = self.tbl_tops.rowCount()
            self.tbl_tops.insertRow(rowPosition)
            self.tbl_tops.setItem(rowPosition , 0, QTableWidgetItem(self.tops[-1][0]))
            self.tbl_tops.setItem(rowPosition , 1, QTableWidgetItem(str(self.tops[-1][1])))

    def calculate_elastic_logs(self):
        if 'Sonic' in self.las.curves:
#            self.w.data["VelComp"] = 1000000/self.w.df()['DT'].values
            self.las.append_curve("VelComp",1000000/self.las['Sonic'],unit="m/s")
        if 'ShearSonic' in self.las.curves:
            self.las.append_curve("VelShear",1000000/self.las['ShearSonic'],unit="m/s")
#            self.w.data["VelShear"]= 1000000/self.w.df()['DTS'].values
        
        elastic=bruges.rockphysics.moduli_dict(self.las['VelComp'],self.las["VelShear"],self.las["Density"])
        self.las.append_curve("BulkModulus",elastic["bulk"],unit="Pa")
        self.las.append_curve("ImpedComp",elastic["imp"],unit="Kg/m3*m/s")
        self.las.append_curve("Lambda",elastic["lam"],unit="Pa")
        self.las.append_curve("Mu",elastic["mu"],unit="Pa")
        self.las.append_curve("CompModulus",elastic["pmod"])
        self.las.append_curve("PoissonRatio",elastic["pr"])
        self.las.append_curve("YoungsModulus",elastic["youngs"],unit="Pa")
        self.las.append_curve("VPVS",self.las["VelComp"]/self.las["VelShear"],unit="")

        
    def plottops(self):
        for tp in self.tops:
#            self.gvPlotzoi.addLine(x=None, y=tp[1])
#            self.gvPlotzoi.addLine(x=None, y=tp[1])
#            self.gvPlot1.addLine(x=None, y=tp[1])
#            self.gvPlot2.addLine(x=None, y=tp[1])
#            self.gvPlot3.addLine(x=None, y=tp[1])
#            self.gvPlot4.addLine(x=None, y=tp[1])
            for plt in self.plots:
                plt.addLine(x=None, y=tp[1])
           

    def getfilename(self):
        path = sys.path[-1]
        fname = QFileDialog.getOpenFileName(self, 'Open file',
                                            path, "LAS file (*.las)")
#        self.le_filename.setText(str(fname[0].replace('\\', '/')))
        self.las_filename = str(fname[0].replace('\\', '/'))

#        self.cb_plot1.clear()
#        self.cb_plot2.clear()
#        self.cb_plot3.clear()
#        self.cb_plot4.clear()
        self.cb_x.clear()
        self.cb_y.clear()
        self.cb_points.clear()

#        self.gvPlot1.clear()
#        self.gvPlot2.clear()
#        self.gvPlot3.clear()
#        self.gvPlot4.clear()

        self.gvLogs.clear()

    def loadlas(self):
        AppMainWindow.getfilename(self);
#        filename = self.le_filename.text()
        self.las = lasio.read(self.las_filename)
        
        self.cbLogDisplay.clear();
        for crv in self.las.curves:
            if crv.mnemonic != "DEPT":
                name, mnemonic, min1, max1, reversed1, units,colour  = AppMainWindow.Find_Curve_Data(crv.mnemonic,curves_info);
                self.las.curves.minimum = min1
                self.las.curves.maximum = max1
                self.las.curves.reversed = reversed1
                self.las.curves.units = units
                self.las.curves.colour = colour
            
                if name is None:
                    name = crv.mnemonic

                  
                crv.mnemonic = name;
                
#                print('crv',crv.mnemonic,crv.unit)
                df=self.las.df();
                if (crv.unit.lower() == "ohm.m"):
                    crv.unit = "ohm-m"
                if (crv.unit.lower() == "us/ft"):
#                    print("here1",crv.mnemonic)
                    df[crv.mnemonic] = AppMainWindow.ConvertCurveToMetric(df[crv.mnemonic],conversion=3.281);
#                    df[crv.mnemonic] = df[crv.mnemonic] * 3.281;
                    self.las.set_data_from_df(df)
                if (crv.unit.lower() == "g/cm3" or crv.unit.lower() == "gm/cc"):
#                    print("here1",crv.mnemonic)
                    df[crv.mnemonic] = AppMainWindow.ConvertCurveToMetric(df[crv.mnemonic],conversion=1000);
#                    df[crv.mnemonic] = df[crv.mnemonic] * 1000;
                    self.las.set_data_from_df(df)

#            self.cb_plot1.addItem(name)
#            self.cb_plot2.addItem(name)
#            self.cb_plot3.addItem(name)
#            self.cb_plot4.addItem(name)
                self.cb_x.addItem(name)
                self.cb_y.addItem(name)
                self.cb_points.addItem(name)

            
        
        for c in curve_displ:
#            print(c['name'],c['curves'])
            self.cbLogDisplay.addItem(c['name'])

        AppMainWindow.calculate_elastic_logs(self);

        print(self.las.df().describe())
        
        self.w = Well.from_lasio(self.las)
#        mainWnd.setWindowTitle("UWI: " + self.w.las.header['Well']['UWI'].value)
        mainWnd.setWindowTitle(mainWnd.windowTitle() + "   File: " + self.las_filename +  "   UWI: " + self.w.las.header['Well']['UWI'].value)

    def plotlasOLD(self):
        y = self.w.survey_basis()

        x = self.w.data[self.w.df().columns[self.cb_plot1.currentIndex()]]
#        name, mnemonic, min1, max1, reversed1,units,colour  = AppMainWindow.Find_Curve_Data(self.w.df().columns[self.cb_plot1.currentIndex()],curves_info);

        self.gvPlot1.clear()
        self.gvPlot1.plot(x, y, pen=(1, 4))
        self.gvPlot1.invertY(True)
        self.gvPlot1.setTitle(self.w.df().columns[self.cb_plot1.currentIndex()])
        self.gvPlot1.setMouseEnabled(x=False, y=True)

        x = self.w.data[self.w.df().columns[self.cb_plot2.currentIndex()]]
        self.gvPlot2.clear()
        self.gvPlot2.plot(x, y, pen=(2, 4))
        self.gvPlot2.invertY(True)
        self.gvPlot2.setTitle(self.w.df().columns[self.cb_plot2.currentIndex()])
        self.gvPlot2.setYLink(self.gvPlot1)
        self.gvPlot2.setMouseEnabled(x=False, y=True)

        x = self.w.data[self.w.df().columns[self.cb_plot3.currentIndex()]]
        self.gvPlot3.clear()
        self.gvPlot3.plot(x, y, pen=(3, 4))
        self.gvPlot3.invertY(True)
        self.gvPlot3.setTitle(self.w.df().columns[self.cb_plot3.currentIndex()])
        self.gvPlot3.setYLink(self.gvPlot1)
        self.gvPlot3.setMouseEnabled(x=False, y=True)

        x = self.w.data[self.w.df().columns[self.cb_plot4.currentIndex()]]
        self.gvPlot4.clear()
        self.gvPlot4.plot(x, y, pen=(4, 4))
        self.gvPlot4.invertY(True)
        self.gvPlot4.setTitle(self.w.df().columns[self.cb_plot4.currentIndex()])
        self.gvPlot4.setYLink(self.gvPlot1)
        self.gvPlot4.setMouseEnabled(x=False, y=True)

        self.gvPlotzoi.clear()
        self.gvPlotzoi.invertY(True)
        self.gvPlotzoi.setTitle("ZOI")
        self.gvPlotzoi.setYLink(self.gvPlot1)
        self.gvPlotzoi.setMouseEnabled(x=False, y=True)
        self.gvPlotzoi.setLimits(xMin=0, xMax=100)
        self.ROItest = None
        
    def plotlas(self):
        self.gvLogs.clear()
        self.plots.clear()
        plottedlogs = [d for d in curve_displ if d['name'] == self.cbLogDisplay.currentText()]
#        print('cbLogDisplay',self.cbLogDisplay.currentText(),'plottedlogs',plottedlogs)
#        print('plottedlogs',plottedlogs[0]['curves'])

        y = self.w.survey_basis()
        
#        print(self.w.df().describe())

        i=0
        for cv in plottedlogs[0]['curves']:
            plt = self.gvLogs.addPlot(name="Logs" + str(i))
            self.plots.append(plt);

            if (type(cv) == list):
                title=cv[0]
                for c in cv:
                    name, mnemonic, min1, max1, reversed1,units,colour  = AppMainWindow.Find_Curve_Data(c,curves_info,search='name');
                    x = self.w.df()[c].values
                    plt.plot(x, y,pen=QtGui.QColor(colour))
            else:
                name, mnemonic, min1, max1, reversed1,units,colour  = AppMainWindow.Find_Curve_Data(cv,curves_info,search='name');
                title=cv
                x = self.w.df()[cv].values
                plt.plot(x, y,pen=QtGui.QColor(colour))
           
                
            plt.invertY(True)
            plt.setTitle(title)
            plt.setMouseEnabled(x=False, y=True)
#            plt.setXRange(float(min1),float(max1))
            if (i > 0):
                plt.setYLink('Logs0')
                plt.hideAxis('left')
            i=i+1
            
        plt_roi = self.gvLogs.addPlot(name="ROI")
#        self.plots.append([i, plt_roi]);
        self.plots.append(plt_roi);

        plt_roi.invertY(True)
        plt_roi.setTitle("ZOI")
        plt_roi.setYLink('Logs0')
        plt_roi.setMouseEnabled(x=False, y=True)
        plt_roi.setLimits(xMin=0, xMax=100)
        plt_roi.hideAxis('left')
        self.ROItest = None

#        print('logs',self.plots)


        def updatecrossplot():
            if self.crossplotisdispayed:
                minindx = (np.abs(self.w.survey_basis() - zoiregion.getRegion()[0])).argmin()
                maxindx = (np.abs(self.w.survey_basis() - zoiregion.getRegion()[1])).argmin()

                if self.ROItest is None:
                    self.ROItest = True
                else:
                    self.scatter.removeItem(self.zoiplot)

                self.zoiplot = pg.ScatterPlotItem(self.w.data[self.w.df().columns[self.cb_x.currentIndex()]][minindx:maxindx],
                                                  self.w.data[self.w.df().columns[self.cb_y.currentIndex()]][minindx:maxindx],
                                                  symbol='+', size=6, brush='r', pen=pg.mkPen(None))
                self.scatter.addItem(self.zoiplot)


        zoiregion = pg.LinearRegionItem([max(y) / 2., max(y) * 2 / 3], orientation=pg.LinearRegionItem.Horizontal)

        self.plots[-1].addItem(zoiregion)

        zoiregion.sigRegionChanged.connect(updatecrossplot)

    def startcrossplot(self):

#        import matplotlib
        from matplotlib import cm

        self.crossplotisdispayed = True  # tells ZOI that crossplot is displaying data

        x = self.w.data[self.w.df().columns[self.cb_x.currentIndex()]]
        y = self.w.data[self.w.df().columns[self.cb_y.currentIndex()]]
        color = self.w.data[self.w.df().columns[self.cb_points.currentIndex()]]

        clrs = color/max(color)          # scale color for cmap, needs to be 0to1
        clrs = [x if x < 1 else 1 for x in clrs]
        cmap = cm.get_cmap('terrain')     # sets cmap to terrain, can be any matplotlib colormap
        c1 = cmap(clrs, bytes=True)  # calls rbg from cmap

        self.scatter.clear()
        data1 = self.scatter.plot()
        data1.setData(x, y, pen=None, symbol='o', symbolPen=None, symbolSize=5, symbolBrush=[pg.mkBrush(c) for c in c1], pxMode=True)
        self.scatter.setLabel('bottom', self.w.df().columns[self.cb_x.currentIndex()])
        self.scatter.setLabel('left', self.w.df().columns[self.cb_y.currentIndex()])

    def plottrendline(self):
        x = np.array(self.w.data[self.w.df().columns[self.cb_x.currentIndex()]])
        y = np.array(self.w.data[self.w.df().columns[self.cb_y.currentIndex()]])

        idx = np.isfinite(x) & np.isfinite(y)
        fit = np.polyfit(x[idx], y[idx], 1)
#        slope, intercept = fit
        self.trendline_slope, self.trendline_intercept = fit
        print('fit',self.trendline_slope, self.trendline_intercept)
        self.le_trendlineslope.setText(str(self.trendline_slope))
        self.le_trendlineint.setText(str(self.trendline_intercept))
        xfit = [min(x[idx]), max(x[idx])]
        yfit = [self.trendline_slope*xx + self.trendline_intercept for xx in xfit]
        self.scatter.plot(xfit, yfit, pen='r')
        self.updateSliders();
        
        
    def updateSliders(self):
#        self.hzScrollBar_slope.setMinimum(self.trendline_slope*0.1);
#        self.hzScrollBar_slope.setMaximum(self.trendline_slope*1.1);
#        self.hzScrollBar_slope.setValue(self.trendline_slope);
#        self.hzScrollBar_intercept.setMinimum(self.trendline_intercept*0.1);
#        self.hzScrollBar_intercept.setMaximum(self.trendline_intercept*1.1);
#        self.hzScrollBar_intercept.setValue(self.trendline_intercept);

        self.hzSlider_slope.setMinimum(self.trendline_slope*0.1);
        self.hzSlider_slope.setMaximum(self.trendline_slope*1.9);
        self.hzSlider_slope.setValue(self.trendline_slope);

        self.hzSlider_intercept.setMinimum(self.trendline_intercept*0.1);
        self.hzSlider_intercept.setMaximum(self.trendline_intercept*1.9);
        self.hzSlider_intercept.setValue(self.trendline_intercept);
        print('slope',self.hzSlider_slope.minimum(),self.hzSlider_slope.maximum())
        print('intercept',self.hzSlider_intercept.minimum(),self.hzSlider_intercept.maximum())
        print('intercept',self.trendline_intercept*0.1,self.trendline_intercept*1.9)

    def Slidervaluechange(self):
        self.trendline_slope = self.hzSlider_slope.value()
        self.trendline_intercept = self.hzSlider_intercept.value()
        self.le_trendlineslope.setText(str(self.trendline_slope))
        self.le_trendlineint.setText(str(self.trendline_intercept))
#        self.l1.setFont(QFont("Arial",size))

    def clickabout(self):
        QMessageBox.about(self, "About", "Created by calgeopy\nMarch, 2018")

#added by C. Hooge    
    def CheckMnemonic(crv,lascrvs,curves_info):
        orig_mn = crv.mnemonic;
        pos = [0]
        if crv.mnemonic != "DEPT":
            name,mnemonic = AppMainWindow.Find_Curve_Data(crv.mnemonic,curves_info)
#        print('mnemonic check',orig_mn,name,mnemonic)
            if name is not None:
                txt_alias2 = ".//*[@name='" + name + "']/Aliases/Name"
                crv_fnd_all = curves_info.findall(txt_alias2)
                pos = [i for i,x in enumerate(crv_fnd_all) if x.text==orig_mn]
        
#            print("hereA",name,orig_mn,pos,len(pos),(name in lascrvs))
                       
                if (mnemonic is not None):
                    if (name in lascrvs):
                        if (len(pos) > 0):
                            crv.mnemonic = name + "_" + str(pos[0])
                        else:
                            crv.mnemonic = name + "_0"
                    
#                crv.mnemonic = name
                    else:
                        crv.mnemonic = name
                
#        crv.original_mnemonic = orig_mn
        else:
            name = 'Depth'
            crv.mnemonic = name  
 
        crv.original_mnemonic = orig_mn
        
        return crv

    def Find_Curve_Data(crv,curves_info,search='mnemonic'):
        if (search == 'mnemonic'):
            txt ='Curve[Mnemonic="' + crv + '"]'
            txt_alias = "Curve/Aliases[Name='" + crv + "']"
        if (search == 'name'):
#            txt ='Curve[Name="' + crv + '"]'
            txt = "Curve[@name='" + crv + "']"
            txt_alias = ""

        crv_fnd = curves_info.find(txt)
        print('search',search,crv,txt,crv_fnd)

        name=None
        mnemonic=None
        min1=None
        max1=None
        reversed1=None
        units=None
        colour=None
        if crv_fnd is not None:
            name=crv_fnd.attrib['name']
            mnemonic = crv_fnd.findtext('Mnemonic')
            min1=crv_fnd.findtext('Minimum')
            max1=crv_fnd.findtext('Maximum')
            reversed1=crv_fnd.findtext('Reversed')
            units=crv_fnd.findtext('Units')
            colour=crv_fnd.findtext('Colour')
        else:
            crv_fnd = curves_info.find(txt_alias)        
            if crv_fnd is not None:
                name=crv_fnd.getparent().attrib['name']
                mnemonic=crv_fnd.getparent().findtext('Mnemonic')
                min1=crv_fnd.getparent().findtext('Minimum')
                max1=crv_fnd.getparent().findtext('Maximum')
                reversed1=crv_fnd.getparent().findtext('Reversed')
                units=crv_fnd.getparent().findtext('Units')
                colour=crv_fnd.getparent().findtext('Colour')
            
        return  name, mnemonic, min1, max1, reversed1,units,colour
    
    def ConvertCurveToMetric(crv_data,conversion=1):
        return crv_data * conversion
        
    
#added by C. Hooge    
#    def menusetup(self):
#        menusetup = QDialogClass()
#        menusetup.exec_()        
        #loadUi("deerfoot_setup.ui", self)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWnd = AppMainWindow()

    # Attach the File->Exit menu item to the slot to close the window
    mainWnd.actionExit.triggered.connect(mainWnd.close)

    # Show the window
    mainWnd.show()

    # Start the main messageloop
    sys.exit(app.exec_())