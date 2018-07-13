import sys
import os
from typing import Set, Any

import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pandas as pd
import bruges
import lasio
from welly import Well
import lxml


from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, QListWidgetItem, QTableWidgetItem,
                             QMessageBox, QLabel)

from PyQt5.uic import loadUi

curves_info = lxml.etree.parse(os.path.join(os.path.dirname(sys.argv[0]),'CurveData.xml')).getroot()

curve_displ = [{'name': 'Son-Den', 'curves': [['GammaRay', 'SelfPot'], ['Sonic'], ['Density']]}]
curve_displ.append({'name': 'Son-Shear', 'curves': [['GammaRay', 'SelfPot'], ['Sonic'], ['ShearSonic']]})
curve_displ.append({'name': 'Resistivity', 'curves': [['GammaRay', 'SelfPot'], ['DeepRes', 'MedRes', 'ShallowRes']]})
curve_displ.append({'name': 'Porosity-Lime', 'curves': [['GammaRay', 'SelfPot'], ['DenPorLime', 'NeutPorLime']]})
curve_displ.append({'name': 'Porosity-Sand', 'curves': [['GammaRay', 'SelfPot'], ['DenPorSand', 'NeutPorSand']]})
curve_displ.append({'name': 'Porosity-Dol', 'curves': [['GammaRay', 'SelfPot'], ['DenPorDol', 'NeutPorDol']]})
#curve_displ.append({'name': 'LMR', 'curves': [['GammaRay', 'SelfPot'], ['Lambda'], ['Mu'],['Density']]})
curve_displ.append({'name': 'LMR', 'curves': [['GammaRay', 'SelfPot'],['Density'], ['LambdaRho'], ['MuRho']]})
curve_displ.append({'name': 'MiniPlot-Lime', 'curves': [['GammaRay', 'SelfPot'], ['DeepRes', 'MedRes', 'ShallowRes'], ['DenPorLime', 'NeutPorLime']]})
curve_displ.append({'name': 'MiniPlot-Sand', 'curves': [['GammaRay', 'SelfPot'], ['DeepRes', 'MedRes', 'ShallowRes'], ['DenPorSand', 'NeutPorSand']]})
curve_displ.append({'name': 'MiniPlot-Dol', 'curves': [['GammaRay', 'SelfPot'], ['DeepRes', 'MedRes', 'ShallowRes'], ['DenPorDol', 'NeutPorDol']]})

xplot_displ = [{'name': 'Son-Den', 'x': 'Sonic', 'y': 'Density', 'drape' : 'Density'}]
xplot_displ.append({'name': 'Son-Shear', 'x':  'Sonic', 'y':  'ShearSonic', 'drape' : 'Density'})

class AppMainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        loadUi(os.path.join(os.path.dirname(sys.argv[0]),"deerfoot.ui"), self)

        self.actionAbout.triggered.connect(self.clickabout)
        self.actionSetup_2.triggered.connect(self.SetupDialog)

#        self.btnGetfilename.clicked.connect(self.getfilename)
        self.btn_loadlas.clicked.connect(self.loadlas)
        self.actionLoad_LAS_File.triggered.connect(self.loadlas)
        self.btnPlotlas.clicked.connect(self.plotlas)

        self.btn_addtop.clicked.connect(self.addtop)
        self.btn_plottops.clicked.connect(self.plottops)
        self.btn_removetop.clicked.connect(self.removetop)

        # self.btn_test.clicked.connect(self.btntest)

        #added by C. Hooge
        self.btn_loadtops.clicked.connect(self.loadtops)
 #       self.le_trendlineslope.textChanged.connect(self.LETextChange)
 #       self.le_trendlineint.textChanged.connect(self.LETextChange)
        self.btn_savetrend.clicked.connect(self.savetrend)

        self.btn_startcrossplot.clicked.connect(self.startcrossplot)
        self.btn_trendline.clicked.connect(self.plottrendline)

        self.btn_updatetrend.clicked.connect(self.updatetrendline)
        
        self.tops = []
        self.plots = []
        self.crossplotisdispayed = False
        
    # self.hzSlider_slope.valueChanged.connect(self.Slidervaluechange)


#added by C. Hooge    
    def SetupDialog(self):
        self.ui = loadUi("setup.ui")
        self.ui.show()
        
    def removetop(self):
        remtop = self.tbl_tops.currentRow()
        self.tops.remove(self.tops[remtop])

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
        self.tbl_tops.setItem(rowPosition, 0, QTableWidgetItem(self.tops[-1][0]))
        self.tbl_tops.setItem(rowPosition, 1, QTableWidgetItem(str(self.tops[-1][1])))
        
# added by C. Hooge
    def loadtops(self):
        path = sys.path[-1]
        tp = QFileDialog.getOpenFileName(self, 'Open file',
                                            path, "Tops file (*.csv *.xlsx)")
        topsfile = tp[0].replace('\\', '/')
#        self.tp_filename.setText(str(topsfile[0].replace('\\', '/')))
#        print('here',topsfile.endswith('.csv'))

        if topsfile.endswith('.xlsx'):
            topdata = pd.read_excel(topsfile, index_col=0)
        if topsfile.endswith('.csv'):
            topdata = pd.read_csv(topsfile, index_col=0)
#        uwi = self.w.las.header['Well']['UWI'].value
#         print(topdata)
        well_tops = topdata[(topdata.index == self.w.las.header['Well']['UWI'].value)]
        well_tops = well_tops.drop(['KB'], axis=1).squeeze().to_dict()
        
        for key, value in well_tops.items():
#            print('t',key,value)
            self.tops.append([key, value])

            rowPosition = self.tbl_tops.rowCount()
            self.tbl_tops.insertRow(rowPosition)
            self.tbl_tops.setItem(rowPosition, 0, QTableWidgetItem(self.tops[-1][0]))
            self.tbl_tops.setItem(rowPosition, 1, QTableWidgetItem(str(self.tops[-1][1])))

    def calculate_elastic_logs(self):
        if 'Sonic' in self.las.curves:
            self.las.append_curve("VelComp", 1000000/self.las['Sonic'], unit="m/s")
        if 'ShearSonic' in self.las.curves:
            self.las.append_curve("VelShear", 1000000/self.las['ShearSonic'], unit="m/s")

        if 'Sonic' in self.las.curves and 'Density' in self.las.curves and 'ShearSonic' in self.las.curves:
            elastic = bruges.rockphysics.moduli_dict(self.las['VelComp'], self.las["VelShear"], self.las["Density"])
            self.las.append_curve("BulkModulus", elastic["bulk"], unit="Pa")
            self.las.append_curve("ImpedComp", elastic["imp"], unit="Kg/m3*m/s")
            self.las.append_curve("Lambda", elastic["lam"], unit="Pa")
            self.las.append_curve("Mu", elastic["mu"], unit="Pa")
            self.las.append_curve("CompModulus", elastic["pmod"])
            self.las.append_curve("PoissonRatio", elastic["pr"])
            self.las.append_curve("YoungsModulus", elastic["youngs"], unit="Pa")
            self.las.append_curve("VPVS", self.las["VelComp"]/self.las["VelShear"], unit="")
            self.las.append_curve("LambdaRho", elastic["lam"]*self.las["Density"]/1000000000000, unit="Pa")
            self.las.append_curve("MuRho", elastic["mu"]*self.las["Density"]/1000000000000, unit="Pa")

    def plottops(self):
        for tp in self.tops:
            for plt in self.plots:
                plt.addLine(x=None, y=tp[1])
           
    def getfilename(self):
        path = sys.path[-1]
        fname = QFileDialog.getOpenFileName(self, 'Open file', path, "LAS file (*.las)")
#        self.le_filename.setText(str(fname[0].replace('\\', '/')))
        self.las_filename = str(fname[0].replace('\\', '/'))

        self.cb_x.clear()
        self.cb_y.clear()
        self.cb_points.clear()

        self.gvLogs.clear()

    def loadlas(self):
        self.getfilename()
#        filename = self.le_filename.text()
        self.las = lasio.read(self.las_filename)
        
        self.cbLogDisplay.clear()
        for crv in self.las.curves:
            if crv.mnemonic != "DEPT":
 #               name, mnemonic, min1, max1, reversed1, units, plottype,colour = helperFunctions.Find_Curve_Data(crv.mnemonic,curves_info,search='mnemonic')
                crvdata = helperFunctions.Find_Curve_Data(crv.mnemonic,curves_info,search='mnemonic')
                self.las.curves.minimum = crvdata['Minimum']
                self.las.curves.maximum = crvdata['Maximum']
                self.las.curves.reversed = crvdata['Reversed']
                self.las.curves.units = crvdata['Units']
                self.las.curves.plottype = crvdata['PlotType']
                self.las.curves.colour = crvdata['Colour']

                if crvdata['Name'] is None:
                    crvdata['Name'] = crv.mnemonic

                crv.mnemonic = crvdata['Name']

#                print('crv',crv.mnemonic,crv.unit,plottype)
                df = self.las.df()
                if crv.unit.lower() == "ohm.m":
                    crv.unit = "ohm-m"
                if crv.unit.lower() == "us/ft":
                    df[crv.mnemonic] = helperFunctions.ConvertCurveToMetric(df[crv.mnemonic],conversion=3.281)
                    self.las.set_data_from_df(df)
                if crv.unit.lower() == "g/cm3" or crv.unit.lower() == "gm/cc":
                    df[crv.mnemonic] = helperFunctions.ConvertCurveToMetric(df[crv.mnemonic], conversion=1000)
                    self.las.set_data_from_df(df)


        self.calculate_elastic_logs()
        for crv in self.las.curves:
            if crv.mnemonic != "DEPT":
                self.cb_x.addItem(crv.mnemonic)
                self.cb_y.addItem(crv.mnemonic)
                self.cb_points.addItem(crv.mnemonic)

        self.curve_displ_new = []
        for cd in curve_displ:
            self.cbLogDisplay.addItem(cd['name'])
            new_list = helperFunctions.CheckCurvesDisplay(cd, self.las.curvesdict)
            z = {**{'name': cd['name']}, **{'curves': new_list}}
            self.curve_displ_new.append(dict(z))

        # print("here",self.curve_displ_new)
 #        print(self.las.df().describe())
        
        self.w = Well.from_lasio(self.las)
        mainWnd.setWindowTitle(mainWnd.windowTitle() + "   File: " + self.las_filename + "   UWI: " + self.w.las.header['Well']['UWI'].value)

    def plotlas(self):
        self.gvLogs.clear()
        self.plots.clear()
#        plottedlogs = [d for d in curve_displ if d['name'] == self.cbLogDisplay.currentText()]
        plottedlogs = [d for d in self.curve_displ_new if d['name'] == self.cbLogDisplay.currentText()]
        print(self.w.df().describe())

        y = self.w.survey_basis()

        i = 0
        for cv in plottedlogs[0]['curves']:
            plt = self.gvLogs.addPlot(name="Logs" + str(i))
            self.plots.append(plt)
            crvdata = []
            for c in cv:
#                    name, mnemonic, min1, max1, reversed1,units,plottype,colour  = helperFunctions.Find_Curve_Data(c, curves_info,
#                                                                                                        search='name')
                crvdata.append(helperFunctions.Find_Curve_Data(c, curves_info,search='name'))
                x = self.w.df()[c].values
                print('c',c,crvdata[-1]['Colour'])
                plt.plot(x, y,pen=QtGui.QColor(crvdata[-1]['Colour']))
                if (crvdata[-1]['PlotType'] == "Logarithmic"):
                    plt.setLogMode(x=True, y=False)

            print('h    ',crvdata[0]['Colour'])

            plt.invertX(helperFunctions.str2bool(crvdata[0]['Reversed']))
            plt.setXRange(float(crvdata[0]['Minimum']),float(crvdata[0]['Maximum']), padding=0)
            plt.invertY(True)
            plt.setTitle(cv[0])
            plt.setMouseEnabled(x=False, y=True)
            plt.showGrid(x=True, y=True)
            #            plt.setXRange(float(min1),float(max1))
            if (i > 0):
                plt.setYLink('Logs0')
                plt.hideAxis('left')
            i=i+1
            
        plt_roi = self.gvLogs.addPlot(name="ROI")
        self.plots.append(plt_roi)

        plt_roi.invertY(True)
        plt_roi.setTitle("ZOI")
        plt_roi.setYLink('Logs0')
        plt_roi.setMouseEnabled(x=False, y=True)
        plt_roi.setLimits(xMin=0, xMax=100)
        plt_roi.hideAxis('left')
        self.ROItest = None


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

        self.trendline_slope, self.trendline_intercept = fit
#        print('fit',self.trendline_slope, self.trendline_intercept)
        self.le_trendlineslope.setText(str(self.trendline_slope))
        self.le_trendlineint.setText(str(self.trendline_intercept))
        xfit = [min(x[idx]), max(x[idx])]
        yfit = [self.trendline_slope*xx + self.trendline_intercept for xx in xfit]
        self.trend=self.scatter.plot(xfit, yfit, pen='r',name='t')

        self.slope_minimum = self.trendline_slope * 0.5
        self.slope_maximum = self.trendline_slope * 1.5
        self.intercept_minimum = self.trendline_intercept * 0.5
        self.intercept_maximum = self.trendline_intercept * 1.5
        self.updateSliders()
        
    def updatetrendline(self):
#        print('slder change',self.hzSlider_slope.value(),self.hzSlider_intercept.value())

        self.trendline_slope=helperFunctions.determine_slider_real_value(self.hzSlider_slope.value(), self.hzSlider_slope.minimum(),
                                                        self.hzSlider_slope.maximum(),
                                                        self.slope_minimum,self.slope_maximum, format='slider')
        self.trendline_intercept=helperFunctions.determine_slider_real_value(self.hzSlider_intercept.value(), self.hzSlider_intercept.minimum(),
                                                        self.hzSlider_intercept.maximum(),
                                                        self.intercept_minimum,self.intercept_maximum, format='slider')

        x = np.array(self.w.data[self.w.df().columns[self.cb_x.currentIndex()]])
        y = np.array(self.w.data[self.w.df().columns[self.cb_y.currentIndex()]])

        idx = np.isfinite(x) & np.isfinite(y)

        self.Slidervaluechange();

        xfit = [min(x[idx]), max(x[idx])]
        yfit = [self.trendline_slope*xx + self.trendline_intercept for xx in xfit]
#        trend.clear()
        self.scatter.removeItem( self.trend )
        self.trend=self.scatter.plot(xfit, yfit, pen='r')
#        self.updateSliders()

    def savetrend(self):
        # TODO  need better logic to save multiple trends and well to same file
        path = sys.path[-1]
        fname = QFileDialog.getSaveFileName(self, 'Save file', path, "CSV File (*.csv)")
        #        self.le_filename.setText(str(fname[0].replace('\\', '/')))
        self.trend_filename = str(fname[0].replace('\\', '/'))
        print(self.w.las.header['Well']['UWI'].value,self.cb_x.currentText(),self.cb_y.currentText(),self.trendline_slope,self.trendline_intercept)

#        f = open(self.trend_filename, 'a')
#        with open(self.trend_filename, "w") as text_file:
#            text_file.write("UWI,x,y,slope,intercept\n")
#            text_file.write(self.w.las.header['Well']['UWI'].value+","+self.cb_x.currentText()+ "," + self.cb_y.currentText()+ "," + str(self.trendline_slope)+ "," + str(self.trendline_intercept)+"\n")

        f = open(self.trend_filename, 'w')
        f.write("UWI,x,y,slope,intercept\n")
        f.write(self.w.las.header['Well']['UWI'].value+","+self.cb_x.currentText()+ "," + self.cb_y.currentText()+ "," + str(self.trendline_slope)+ "," + str(self.trendline_intercept)+"\n")
        f.close()

    def updateSliders(self):

        self.hzSlider_slope.setValue(
            helperFunctions.determine_slider_real_value(self.trendline_slope, self.hzSlider_slope.minimum(),
                                                self.hzSlider_slope.maximum(), self.slope_minimum, self.slope_maximum))
        self.hzSlider_intercept.setValue(helperFunctions.determine_slider_real_value(self.trendline_intercept,self.hzSlider_intercept.minimum(),self.hzSlider_intercept.maximum(), self.intercept_minimum,self.intercept_maximum))


    def Slidervaluechange(self):
        self.le_trendlineslope.setText(str(self.trendline_slope))
        self.le_trendlineint.setText(str(self.trendline_intercept))
#        self.l1.setFont(QFont("Arial",size))

    def LETextChange(self):
        self.trendline_slope=self.le_trendlineslope.text()
        self.trendline_intercept=self.le_trendlineint.text()
        self.updateSliders()
        self.updatetrendline()

    def clickabout(self):
        QMessageBox.about(self, "About", "Created by calgeopy\nMarch, 2018,\r\nand greatly extended in April - June 2018")

        
#added by C. Hooge    
class helperFunctions:
    def CheckMnemonic(crv,lascrvs,curves_info):
        orig_mn = crv.mnemonic
        pos = [0]
        if crv.mnemonic != "DEPT":
 #           name, mnemonic, min1, max1, reversed1, units, plottype, colour = helperFunctions.Find_Curve_Data(crv.mnemonic,curves_info)
            crvdata = helperFunctions.Find_Curve_Data(crv.mnemonic,curves_info)
#        print('mnemonic check',orig_mn,name,mnemonic)
            if crvdata['Name'] is not None:
                txt_alias2 = ".//*[@name='" + crvdata['Name'] + "']/Aliases/Name"
                crv_fnd_all = curves_info.findall(txt_alias2)
                pos = [i for i,x in enumerate(crv_fnd_all) if x.text==orig_mn]
        
#            print("hereA",name,orig_mn,pos,len(pos),(name in lascrvs))
                       
                if crvdata['Mnemonic'] is not None:
                    if crvdata['Name'] in lascrvs:
                        if len(pos) > 0:
                            crv.mnemonic = crvdata['Name'] + "_" + str(pos[0])
                        else:
                            crv.mnemonic = crvdata['Name'] + "_0"
                    
#                crv.mnemonic = name
                    else:
                        crv.mnemonic = crvdata['Name']
                
#        crv.original_mnemonic = orig_mn
        else:
            name = 'Depth'
            crv.mnemonic = name  
 
        crv.original_mnemonic = orig_mn
        
        return crv

    def Find_Curve_Data(crv_mn,curves_info,search='mnemonic'):
        if search == 'mnemonic':
            txt = 'Curve[Mnemonic="' + crv_mn + '"]'
            txt_alias = "Curve/Aliases[Name='" + crv_mn + "']"
#            txt_alias = "Curve/Aliases[@name='" + crv_mn + "']"
        if (search == 'name'):
            txt = "Curve[@name='" + crv_mn + "']"
            txt_alias = ""

        crv_fnd = curves_info.find(txt)
#        print('search',search,crv_mn,txt,crv_fnd)

        name = None
        mnemonic = None
        min1 = None
        max1 = None
        reversed1 = None
        units = None
        colour = None
        plottype = None
        if crv_fnd is not None:
            name = crv_fnd.attrib['name']
            mnemonic = crv_fnd.findtext('Mnemonic')
            min1 = crv_fnd.findtext('Minimum')
            max1 = crv_fnd.findtext('Maximum')
            reversed1 = crv_fnd.findtext('Reversed')
            units = crv_fnd.findtext('Units')
            colour = crv_fnd.findtext('Colour')
            plottype = crv_fnd.findtext('Type')
        else:
            crv_fnd = curves_info.find(txt_alias)        
            if crv_fnd is not None:
                name = crv_fnd.getparent().attrib['name']
                mnemonic = crv_fnd.getparent().findtext('Mnemonic')
                min1 = crv_fnd.getparent().findtext('Minimum')
                max1 = crv_fnd.getparent().findtext('Maximum')
                reversed1 = crv_fnd.getparent().findtext('Reversed')
                units = crv_fnd.getparent().findtext('Units')
                colour = crv_fnd.getparent().findtext('Colour')
                plottype = crv_fnd.getparent().findtext('Type')

#        return name, mnemonic, min1, max1, reversed1, units, plottype, colour
        return {'Name':name, 'Mnemonic':mnemonic, 'Minimum':min1, 'Maximum': max1, 'Reversed':reversed1, 'Units':units, 'PlotType':plottype, 'Colour':colour}

    def ConvertCurveToMetric(crv_data,conversion=1):
        return crv_data * conversion
        
    def str2bool(v):
        return v.lower() in ("yes", "true", "True", "t", "1")

    def CheckCurvesDisplay(crvs_disp, curvesdict):
#        print("crvs_disp", crvs_disp['curves'])
        new_crvs_list = []
        for cv in crvs_disp['curves']:
            tst = set(cv).intersection(curvesdict)
#            print("cv",cv,tst,list(tst))

            if len(tst) > 0:
                new_crvs_list.append(list(tst))

#        print("cd NEW", new_crvs_list)
        return new_crvs_list

    def determine_slider_real_value(val2, min_slider, max_slider, min_val, max_val, format='value'):
        #           valout = int(val2 * (self.hzSlider_slope.maximum()-self.hzSlider_slope.minimum())/(max_val - min_val))
        # m = (max_slider - min_slider) / (max_val - min_val)
        # b = max_slider - (m * max_val)
        # valout = val2 * m + b
        valout = None
        print('fit2a', format, [min_val, max_val])
        if format == 'value':
            fit = np.polyfit([min_val, max_val], [min_slider, max_slider], 1)
            valout = int(fit[0] * val2 + fit[1])
        if format == 'slider':
            fit = np.polyfit([min_slider, max_slider], [min_val, max_val], 1)
            valout = fit[0] * val2 + fit[1]
        print('fit2',fit,[min_val, max_val])
        return valout


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWnd = AppMainWindow()

    # Attach the File->Exit menu item to the slot to close the window
    mainWnd.actionExit.triggered.connect(mainWnd.close)

    # Show the window
    mainWnd.show()

    # Start the main messageloop
    sys.exit(app.exec_())