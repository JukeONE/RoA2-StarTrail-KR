from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
wb=Workbook()
F='Arial'
H=Font(name=F,bold=True,color='FFFFFF'); HF=PatternFill('solid',fgColor='4F3A2A')
IN=Font(name=F,color='0000FF'); N=Font(name=F); B=Font(name=F,bold=True); T=Font(name=F,bold=True,size=14)
Y=PatternFill('solid',fgColor='FFF2CC')
thin=Side(style='thin',color='BFBFBF'); BD=Border(left=thin,right=thin,top=thin,bottom=thin)
def hdr(ws,row,vals):
    for i,v in enumerate(vals,1):
        c=ws.cell(row=row,column=i,value=v); c.font=H; c.fill=HF; c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True); c.border=BD
def cell(ws,ref,v,font=N,fmt=None,fill=None):
    c=ws[ref]; c.value=v; c.font=font; c.border=BD
    if fmt: c.number_format=fmt
    if fill: c.fill=fill
    return c

# ---- Sheet 1: 분량
ws=wb.active; ws.title='분량 환산'
ws['A1']='아카니아 왕국 2 (Star Trail) 한글패치 — 번역 분량 환산'; ws['A1'].font=T
ws['A2']='파란 글씨 = 직접 바꿀 수 있는 입력값(노란 칸). 검은 글씨 = 계산식.'; ws['A2'].font=Font(name=F,italic=True,color='666666')
hdr(ws,4,['항목','값','단위','근거'])
rows=[
 ('LTX 텍스트 파일 (114개)',440893,'바이트','STAR.DAT에서 추출해 실측'),
 ('TLK 대화 파일 (205개) 인쇄 가능 문자',298364,'바이트','STAR.DAT에서 추출해 실측 (비텍스트 데이터 일부 포함 가능)'),
]
r=5
for name,v,u,src in rows:
    cell(ws,f'A{r}',name); cell(ws,f'B{r}',v,IN,'#,##0',Y); cell(ws,f'C{r}',u); cell(ws,f'D{r}',src); r+=1
cell(ws,'A7','전체 영문 분량',B); cell(ws,'B7','=B5+B6',B,'#,##0'); cell(ws,'C7','바이트'); cell(ws,'D7','합계')
cell(ws,'A8','단어당 평균 바이트 (공백 포함)'); cell(ws,'B8',5.8,IN,'0.0',Y); cell(ws,'C8','바이트/단어'); cell(ws,'D8','가정: 영어 평균 단어 길이 + 공백·문장부호')
cell(ws,'A9','영어 단어 수 (환산)',B); cell(ws,'B9','=B7/B8',B,'#,##0'); cell(ws,'C9','단어'); cell(ws,'D9','전체 바이트 ÷ 단어당 바이트')
cell(ws,'A10','번역 제외 비율 (디버그·중복·비텍스트)'); cell(ws,'B10',0.15,IN,'0%',Y); cell(ws,'C10','비율'); cell(ws,'D10','가정: 10~20% 범위의 중간값. 대화 파일 분석 후 갱신')
cell(ws,'A11','실제 번역 단어 수 (추정)',B); cell(ws,'B11','=B9*(1-B10)',B,'#,##0'); cell(ws,'C11','단어'); cell(ws,'D11','환산 단어 × (1 − 제외 비율)')
for col,w in zip('ABCD',[38,14,12,60]): ws.column_dimensions[col].width=w

# ---- Sheet 2: 기간 추정
w2=wb.create_sheet('기간 추정')
w2['A1']='방식별 예상 기간'; w2['A1'].font=T
w2['A2']='하루 처리량과 검수 기간은 가정값입니다. 노란 칸을 바꾸면 기간이 다시 계산됩니다.'; w2['A2'].font=Font(name=F,italic=True,color='666666')
cell(w2,'A4','실제 번역 단어 수',B); cell(w2,'B4',"='분량 환산'!B11",Font(name=F,color='008000'),'#,##0'); cell(w2,'C4','단어 (분량 환산 시트에서 연결)')
cell(w2,'A5','한 달 작업일 수'); cell(w2,'B5',22,IN,'0',Y); cell(w2,'C5','일 (가정)')
hdr(w2,7,['방식','하루 처리량 최소 (단어)','하루 처리량 최대 (단어)','번역 일수 최소','번역 일수 최대','검수 일수 최소','검수 일수 최대','총 일수 최소','총 일수 최대','총 기간(개월) 최소','총 기간(개월) 최대','비고'])
data=[
 ('사람이 혼자 번역',2000,3000,0,0,'하루 2,000~3,000단어 기준. 검수는 번역 중 병행으로 가정'),
 ('Claude 초벌 + 사용자 검수',None,None,14,28,'초벌 2~4일(직접 입력) + 검수 2~4주. 추천 방식'),
 ('Claude 번역, 검수 없이 출시',None,None,0,0,'2~4일. 용어 불일치·어색한 문장 위험 큼'),
]
r=8
for name,lo,hi,qlo,qhi,note in data:
    cell(w2,f'A{r}',name,B)
    if lo:
        cell(w2,f'B{r}',lo,IN,'#,##0',Y); cell(w2,f'C{r}',hi,IN,'#,##0',Y)
        cell(w2,f'D{r}',f'=ROUNDUP($B$4/C{r},0)',N,'0'); cell(w2,f'E{r}',f'=ROUNDUP($B$4/B{r},0)',N,'0')
    else:
        cell(w2,f'B{r}','-'); cell(w2,f'C{r}','-')
        cell(w2,f'D{r}',2,IN,'0',Y); cell(w2,f'E{r}',4,IN,'0',Y)
    cell(w2,f'F{r}',qlo,IN,'0',Y); cell(w2,f'G{r}',qhi,IN,'0',Y)
    cell(w2,f'H{r}',f'=D{r}+F{r}',B,'0'); cell(w2,f'I{r}',f'=E{r}+G{r}',B,'0')
    cell(w2,f'J{r}',f'=H{r}/$B$5',N,'0.0'); cell(w2,f'K{r}',f'=I{r}/$B$5',N,'0.0')
    cell(w2,f'L{r}',note); r+=1
w2['D9'].comment=Comment('Claude 초벌 번역 기간: 이전 답변의 추정치(2~4일)를 직접 입력','Claude')
for col,w in zip('ABCDEFGHIJKL',[30,14,14,12,12,12,12,12,12,13,13,52]): w2.column_dimensions[col].width=w
w2.row_dimensions[7].height=32

# ---- Sheet 3: 전체 일정
w3=wb.create_sheet('전체 일정')
w3['A1']='1차 한글판까지 전체 일정 (추천 방식 기준)'; w3['A1'].font=T
hdr(w3,3,['단계','작업 내용','최소 (일)','최대 (일)','상태'])
steps=[
 ('사전 작업','대화 파일(TLK 205개) 구조 분석',None,None,'대기'),
 ('사전 작업','추출·삽입 도구 정리 (LTX/TLK → 번역 표 → 재삽입)',None,None,'대기'),
 ('사전 작업','길이 제한 칸 확인 (예: 장소 데이터 17바이트 이름 칸)',None,None,'대기'),
 ('번역','용어집 작성 (신 이름·지명·주문·아이템)',None,None,'대기'),
 ('번역','Claude 초벌 번역',"='기간 추정'!D9","='기간 추정'!E9",'대기'),
 ('검수','사용자 검수 + 게임 안 확인',"='기간 추정'!F9","='기간 추정'!G9",'대기'),
 ('배포','설치·복원 도구 (원본 백업, 적용, 복원)',None,None,'대기'),
]
r=4
for i,(st,job,lo,hi,stt) in enumerate(steps):
    cell(w3,f'A{r}',st); cell(w3,f'B{r}',job)
    if lo: cell(w3,f'C{r}',lo,Font(name=F,color='008000'),'0'); cell(w3,f'D{r}',hi,Font(name=F,color='008000'),'0')
    else: cell(w3,f'C{r}',None,IN,'0',Y); cell(w3,f'D{r}',None,IN,'0',Y)
    cell(w3,f'E{r}',stt); r+=1
# pre-work combined 1~3 days: put on first row, others 0 (combined estimate)
w3['C4'].value=1; w3['D4'].value=3
w3['C4'].comment=Comment('이전 답변: 사전 작업 3가지를 합쳐 1~3일로 추정. 이 행에 합계로 기록','Claude')
for rr in (5,6): w3[f'C{rr}'].value=0; w3[f'D{rr}'].value=0
w3['C5'].comment=Comment('사전 작업 합계(1~3일)에 포함','Claude')
w3['C7'].value=0; w3['D7'].value=0; w3['C7'].comment=Comment('별도 추정 없음 — 필요하면 입력','Claude')
w3['C10'].value=0; w3['D10'].value=0; w3['C10'].comment=Comment('별도 추정 없음 — 필요하면 입력','Claude')
cell(w3,'A12','합계 (일)',B); cell(w3,'C12','=SUM(C4:C10)',B,'0'); cell(w3,'D12','=SUM(D4:D10)',B,'0')
cell(w3,'A13','합계 (주)',B); cell(w3,'C13','=C12/7',B,'0.0'); cell(w3,'D13','=D12/7',B,'0.0')
w3['B13']='달력 기준 (주 7일)'; w3['B13'].font=N
for col,w in zip('ABCDE',[12,58,10,10,10]): w3.column_dimensions[col].width=w

# ---- Sheet 4: 주의사항
w4=wb.create_sheet('검수 포인트')
w4['A1']='검수가 오래 걸리는 이유와 확인할 것'; w4['A1'].font=T
hdr(w4,3,['구분','내용','예시'])
notes=[
 ('용어 통일','신 이름·지명·주문·아이템 이름을 표로 먼저 정해 전체에 똑같이 사용','Peraine → 페라이네'),
 ('게임 안 확인','줄 넘침, 문장 잘림을 실제 화면에서 확인','신전 메뉴, 장소 이름 띠'),
 ('끼워 넣는 문장','%s 자리에 단어가 들어가는 문장의 한국어 어순·조사 처리','"Temple of %s in %s" → "%s 신전 - %s"'),
 ('길이 고정 칸','한글은 한 글자 2바이트라 영어보다 길어질 수 있음','장소 데이터 이름 칸 17바이트'),
 ('기간 변수','검수에 하루 몇 시간을 쓰느냐가 전체 기간을 가장 크게 좌우',''),
]
r=4
for a,b,c in notes:
    cell(w4,f'A{r}',a,B); cell(w4,f'B{r}',b); cell(w4,f'C{r}',c)
    for col in 'ABC': w4[f'{col}{r}'].alignment=Alignment(wrap_text=True,vertical='top')
    r+=1
for col,w in zip('ABC',[16,60,40]): w4.column_dimensions[col].width=w
for s in wb.worksheets: s.freeze_panes=None
wb.save('/mnt/user-data/outputs/roa2/아카니아2_한글패치_기간추정.xlsx')
