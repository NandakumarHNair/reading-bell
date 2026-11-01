#!/usr/bin/env python3
"""Reading Bell UI regression tests. Requires Python and Playwright with Chromium.
Runs the self-contained HTML in a blank, isolated browser document. Timer and
storage tests use controlled adapters; they do not certify locked-device audio.
"""
from pathlib import Path
import json
import os
import shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'index.html').read_text()
QADIR=Path(os.environ.get('READING_BELL_QA',str(ROOT/'tests'/'screenshots')))
QADIR.mkdir(parents=True,exist_ok=True)
MOCK=r'''<script>
(()=>{
 const base=1793451600000;let advance=0;
 Date.now=()=>base+advance;window.advanceTime=ms=>{advance+=ms;document.dispatchEvent(new Event('visibilitychange'));};window.shiftTimeOnly=ms=>advance+=ms;
 const storage=seed=>{const data={...seed};return {getItem:k=>Object.hasOwn(data,k)?data[k]:null,setItem:(k,v)=>data[k]=String(v),removeItem:k=>delete data[k],clear:()=>Object.keys(data).forEach(k=>delete data[k]),dump:()=>({...data})};};
 Object.defineProperty(window,'localStorage',{value:storage(LOCAL_SEED),configurable:true});Object.defineProperty(window,'sessionStorage',{value:storage(SESSION_SEED),configurable:true});
 const param=()=>({value:0,setValueAtTime(){},linearRampToValueAtTime(){},setTargetAtTime(){}});
 class Audio {constructor(){this.created=Date.now();this.state='running';this.destination={};}get currentTime(){return (Date.now()-this.created)/1000;}resume(){this.state='running';return Promise.resolve();}createGain(){return {gain:param(),connect(){},disconnect(){}};}createBiquadFilter(){return {frequency:param(),Q:param(),connect(){},disconnect(){}};}createOscillator(){return {frequency:param(),connect(){},disconnect(){},start(){},stop(){}};}}
 window.AudioContext=Audio;
})();</script>'''

results=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 results.append(name);print('PASS:',name)

def run():
 with sync_playwright() as pw:
  exe=os.environ.get('CHROMIUM_EXECUTABLE') or shutil.which('chromium') or shutil.which('google-chrome')
  opts={'headless':True}
  if exe:opts['executable_path']=exe
  browser=pw.chromium.launch(**opts)
  errors=[]
  def new(local=None,session=None,width=1440):
   page=browser.new_page(viewport={'width':width,'height':1050},timezone_id='Asia/Kolkata')
   page.on('pageerror',lambda e:errors.append(str(e)))
   inject=MOCK.replace('LOCAL_SEED',json.dumps(local or {})).replace('SESSION_SEED',json.dumps(session or {}))
   page.set_content(HTML.replace('<head>','<head>'+inject,1))
   page.wait_for_function('window.ReadingBell')
   return page
  def snap(p):return p.evaluate('ReadingBell.snapshot()')
  def advance(p,ms):p.evaluate('(ms)=>advanceTime(ms)',ms)
  def start(p,pages='8',minutes='30'):
   p.locator('#goalPages').fill(pages);p.locator('#goalMinutes').fill(minutes);p.locator('#startBtn').click();p.wait_for_function('ReadingBell.snapshot().session?.status === "running"')
  def sounds(p,kind):return [s for s in snap(p)['sounds'] if s['kind']==kind and not s['cancelled']]
  p=new();check('Dark default',p.locator('html').get_attribute('data-ui-theme')=='dark')
  check('No repeating chime or popup controls',p.locator('#intervalButtons,#restartIntervalBtn,#overlay,#notifications,#speak').count()==0)
  p.screenshot(path=str(QADIR/'setup-desktop.png'),full_page=True)
  p.locator('#goalPages').fill('0');p.locator('#startBtn').click();check('Reject zero page target',snap(p)['session'] is None)
  start(p);check('One start cue and one scheduled end cue',len(sounds(p,'start'))==1 and len(sounds(p,'end'))==1)
  started=snap(p);advance(p,5*60000);check('No midpoint cues',len(snap(p)['sounds'])==2)
  p.locator('#finishBtn').focus();p.keyboard.press('Space');check('Space pauses even when a button has focus',snap(p)['session']['status']=='paused')
  pause_left=snap(p)['remainingMs'];advance(p,15000);check('Pause freezes remaining time',snap(p)['remainingMs']==pause_left)
  check('Pause cancels old end buzzer',not sounds(p,'end'))
  p.keyboard.press('Space');p.wait_for_function('ReadingBell.snapshot().session.status === "running"')
  check('Resume is silent and schedules new end',len(sounds(p,'start'))==1 and len(sounds(p,'end'))==1)
  check('Resume preserves full remaining time',snap(p)['remainingMs']==pause_left)
  p.keyboard.down('Space');p.keyboard.down('Space');p.keyboard.up('Space');check('Holding Space toggles once',snap(p)['session']['status']=='paused')
  p.keyboard.press('Space');p.wait_for_function('ReadingBell.snapshot().session.status === "running"')
  p.screenshot(path=str(QADIR/'running-desktop.png'),full_page=True)
  advance(p,snap(p)['remainingMs']);check('Natural deadline completes session',snap(p)['session']['status']=='complete')
  check('Finish cue is not duplicated',len(sounds(p,'end'))==1)
  advance(p,180000);check('No repeating finish alarm',len(sounds(p,'end'))==1)
  check('Result prompt appears only after completion',p.locator('#resultForm').is_visible())
  p.locator('#actualPages').fill('6');p.locator('#resultForm button').click();check('6 of 8 gives 75 percent',p.locator('#resultPercent').inner_text()=='75%')
  p.screenshot(path=str(QADIR/'result-desktop.png'),full_page=True)
  p.locator('#editResult').click();p.locator('#actualPages').fill('6.5');p.locator('#resultForm button').click();check('Fractional pages accepted',p.locator('#resultPercent').inner_text()=='81.3%')
  p.locator('#editResult').click();p.locator('#actualPages').fill('10');p.locator('#resultForm button').click();check('Results are not capped at 100 percent',p.locator('#resultPercent').inner_text()=='125%')
  p.locator('#editResult').click();p.locator('#actualPages').fill('0');p.locator('#resultForm button').click();check('Zero actual pages accepted',p.locator('#resultPercent').inner_text()=='0%')
  p.locator('#newSession').click();check('New session returns to editable plan',p.locator('#goalSetup').is_visible() and p.locator('#goalMinutes').input_value()=='30')
  start(p,pages='12',minutes='60');advance(p,30000);p.once('dialog',lambda d:d.accept());p.locator('#resetSessionBtn').click()
  check('Reset retains editable target and duration',p.locator('#goalPages').input_value()=='12' and p.locator('#goalMinutes').input_value()=='60' and snap(p)['session'] is None)
  check('Reset cancels scheduled end buzzer',snap(p)['endScheduledFor'] is None)
  count=len(snap(p)['sounds']);advance(p,7200000);check('Reset does not leave a future buzzer',len(snap(p)['sounds'])==count)
  p.close()
  p=new();start(p,minutes='1');advance(p,10000);p.once('dialog',lambda d:d.accept());p.locator('#finishBtn').click()
  check('Finish early records elapsed time',snap(p)['session']['elapsedMs']==10000 and snap(p)['session']['endedEarly'])
  check('Finish early produces one end cue',len(sounds(p,'end'))==1)
  p.close()
  p=new();start(p,minutes='1');p.evaluate('shiftTimeOnly(60000)');p.once('dialog',lambda d:d.accept());p.locator('#finishBtn').dispatch_event('click');check('Manual finish at the deadline does not double buzz',len(sounds(p,'end'))==1);p.close()
  p=new();p.locator('#volume').fill('0');start(p,minutes='1');advance(p,60000);check('Volume zero is silent at both ends',snap(p)['sounds']==[]);p.close()
  p=new();start(p,minutes='3');advance(p,30000);seeds=p.evaluate('({local:localStorage.dump(),session:sessionStorage.dump()})');deadline=snap(p)['session']['deadline'];p.close()
  p=new(seeds['local'],seeds['session']);advance(p,30000);check('Restore keeps deadline without replaying start sound',snap(p)['session']['deadline']==deadline and snap(p)['sounds']==[])
  check('Restore requests audio permission',p.locator('#enableSound').is_visible())
  p.locator('#enableSound').click();check('Enabling restored audio does not play a start cue',len(sounds(p,'start'))==0 and len(sounds(p,'end'))==1)
  advance(p,150000);check('Restored session completes correctly',snap(p)['session']['status']=='complete');p.close()
  p=new({'reading-bell.settings.v1':json.dumps({'uiTheme':'dark','goalPages':30,'goalMinutes':180,'interval':1,'speak':True,'notifications':True,'sound':'bell','visual':True})})
  check('Legacy targets migrate without restoring old alarms',p.locator('#goalPages').input_value()=='30' and p.locator('#goalMinutes').input_value()=='180' and 'interval' not in snap(p)['settings'])
  p.locator('#settingsBtn').click();p.locator('#tab-appearance').focus();p.keyboard.press('ArrowRight');check('Settings tabs keyboard navigation',p.locator('#tab-screens').get_attribute('aria-selected')=='true');p.locator('#closeSettings').click()
  p.locator('#themeBtn').click();check('Light theme toggle',p.locator('html').get_attribute('data-ui-theme')=='light')
  p.screenshot(path=str(QADIR/'light-desktop.png'),full_page=True);p.close()
  for width in [320,390,768,1024]:
   p=new(width=width);check(f'No horizontal overflow at {width}px',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   if width==390:p.screenshot(path=str(QADIR/'setup-mobile.png'),full_page=True)
   start(p,pages='8',minutes='90');check(f'Active session fits at {width}px',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   if width==390:p.screenshot(path=str(QADIR/'running-mobile.png'),full_page=True)
   advance(p,90*60000);p.locator('#actualPages').fill('6');p.locator('#resultForm button').click();check(f'Result fits at {width}px',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
   if width==390:p.screenshot(path=str(QADIR/'result-mobile.png'),full_page=True)
   p.close()
  check('No runtime JavaScript errors',not errors)
  browser.close()
 print(f'\n{len(results)} checks passed.')
 (QADIR/'test-results.json').write_text(json.dumps({'passed':len(results),'checks':results,'errors':errors},indent=2))

if __name__=='__main__':run()
