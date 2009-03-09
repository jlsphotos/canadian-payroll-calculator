from mechanize import Browser
from lxml import html as HTML
import pprint
import string


ENDPOINT = "https://apps.cra-arc.gc.ca/ebci/rhpd/startLanguage.do?lang=English"


class PayrollCalculator(object):
    """
    Calculate's payroll taxes from the CRA online payroll calculator.
    
    """
    def __init__(self, salary, cpp_to_date, ei_to_date, ei_exempt, payperiod):
        self.payperiod = str(payperiod)
        self.salary = str(salary)
        self.cpp_to_date = str(cpp_to_date)
        self.ei_to_date = str(ei_to_date)
        self.ei_exempt = ei_exempt
        
        # Setup the Mechanize Browser.
        self.b = Browser()
        self.b.set_handle_robots(False)
        self.b.open(ENDPOINT)
        

    def calculate(self):
        # 1) Pay Period
        print "PAY"
        print self.b.geturl()
        self.b.select_form(name="payrollData")
        self.b.form["year"] = ["4"]  # January 1, 2009
        self.b.form["province"] = ["9"]  # British Columbia
        self.b.form["payPeriod"] = [self.payperiod]#["2"]  # Biweekly
        self.b.submit(name="fwdSalary")

        # 2) Salary / Bonus Etc.
        print "SALARY"
        print self.b.geturl()
        self.b.select_form(name="payrollData")
        self.b.form["yearToDateCPPAmount"] = self.cpp_to_date
        self.b.form["yearToDateEIAmount"] = self.ei_to_date
        
        if self.ei_exempt:
            self.b.form["yearToDateEI"] = ["2"]  # EI exempt
        
        self.b.submit(name="fwdGrossSalary")

        # 3) Gross Income
        print "GROSS"
        print self.b.geturl()
        self.b.select_form(name="grossIncomeData")
        self.b.form["incomeTypeAmount"] = self.salary
        self.b.submit()

        # 4) Salary / Bonus Etc. again
        print "SALARY"
        print self.b.geturl()
        self.b.select_form(name="payrollData")
        self.b.submit(nr=3)  # 3 is the magic number for the Calculate button

        # 5) Results page. Scraping time.
        self.doc = HTML.fromstring(self.b.response().read(), self.b.geturl())
        return self._needle()    
    
    def _needle(self):
        # The data we want is trapped somewhere around here.
        fields = ["Salary or wages for the pay period",
                  "Total EI insurable earnings for the pay period",
                  "Taxable income",
                  "Cash income for the pay period",
                  "Federal tax deductions",
                  "Provincial tax deductions",
                  "Requested additional tax deduction",
                  "Total tax on income",
                  "CPP deductions",
                  "EI deductions",
                  "Amounts deducted at source",
                  "Total deductions on income",
                  "Net amount"]
                  
        values = [string2dollar(td.text) for td in self.doc.xpath("//table[3]//td[2]")]
        values.append(string2dollar(self.doc.xpath("//table[4]//td[2]")[0].text))
        
        print string2dollar(self.doc.xpath("//table[4]//td[2]")[0].text)
        
        pprint.pprint(zip(fields, values))
        
        return values
        #return zip(fields, values)
        
        
def string2dollar(s):
    return round(float(''.join(c for c in s if c in string.digits + '.')), 2)