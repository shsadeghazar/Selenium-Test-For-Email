"""رانر جداگانه برای سامانه‌های ناقص، با یک لاگین و یک پنجره Chrome.

این فایل متعلق به نسخه اصلی mail_runner نیست. ابتدا ورود واقعی را انجام می‌دهد
و سپس سناریوها را در همان مرورگر اجرا می‌کند. هیچ session.json، تزریق کوکی،
localStorage/sessionStorage یا robots.txt میان سناریوها اجرا نمی‌شود.
"""

from __future__ import annotations

import base64
import os
import traceback
import zlib
from pathlib import Path

from selenium import webdriver


APP_DIR = Path(__file__).resolve().parent
os.chdir(APP_DIR)

SCRIPT_ORDER = [('لاگین', 'login.py'),
 ('ارسال ایمیل ساده', 'test_send_email.py'),
 ('ارسال ایمیل با پیوست', 'test_send_with_attachment.py'),
 ('ارسال ایمیل با پیوست و امضا', 'test_send_mail_with_signature.py'),
 ('ذخیره پیش\u200cنویس همراه با پیوست', 'test_save_draft_with_attachment.py'),
 ('ارسال پیش\u200cنویس ذخیره\u200cشده', 'test_send_saved_draft.py'),
 ('ریپلای ساده به اولین ایمیل', 'test_reply_email.py'),
 ('ریپلای پیشرفته با پیوست', 'test_reply_with_attachment.py'),
 ('ریپلای پیشرفته با امضا', 'test_reply_with_signature.py'),
 ('ساخت پوشه', 'test_create_folder.py'),
 ('ساخت پوشه و انتقال ایمیل', 'test_folder_and_move.py'),
 ('چرخه پوشه در صندوق ارسال', 'test_folder_lifecycle_in_sent.py'),
 ('خوانده/نخوانده در صندوق ورودی', 'test_mark_read_unread.py'),
 ('انتقال به هرزنامه', 'test_move_to_spam.py'),
 ('ریپلای از صندوق ارسال با پیوست', 'test_reply_with_attachment_from_sent.py'),
 ('خوانده/نخوانده در صندوق ارسال', 'test_mark_read_unread_sent.py')]

SOURCE_SHA256 = {'login.py': '84512c59aad4c66fc4de0fd16914d702556574f7b3ab5a0f7a430d697abfc390',
 'test_send_email.py': '82b939d58ae621392115de792528418333fd8e8a90f2d2c2901dd21280c0db3f',
 'test_send_with_attachment.py': '5f7455ce995a7fa7c5ea96996953592ac8549941e33a719c138b919a37e1e8ba',
 'test_send_mail_with_signature.py': '682da0f443bef8fbe4d372e6382e72318f3481e99cb605ebe77485123947d9e5',
 'test_save_draft_with_attachment.py': 'c0895e14e3e8511211cb400d6c4090725c90f560bc09a898341908438ad07b80',
 'test_send_saved_draft.py': '01aecfa319bac242ba6c3a4d290a64ed9f48be75a507a759defe33ec022874f9',
 'test_reply_email.py': 'c747f6e501bd25c392d4091df303c8bee9e54e3f002fab817902ff2957db1ff2',
 'test_reply_with_attachment.py': '5710aa13e930740fe052554debef6e745092f35e2cb38abaccbe027d11cda373',
 'test_reply_with_signature.py': '6807f84eefee5272506c877268a038c30f01caa1686594cd87dd0eb56652110c',
 'test_create_folder.py': 'b862bd11a3d15b245661b1afeba984c2ee8be73f589f53ee5eccb7eeb64437d4',
 'test_folder_and_move.py': 'cbfe84d49a1a646709cbd6b021a5aaf14744983a186be65b6aaff6939bdf9022',
 'test_folder_lifecycle_in_sent.py': 'a11e4490a490eb025291062401af630ce451f90a929f3d68777612ad949ac29c',
 'test_mark_read_unread.py': 'cfeb61fa25bb5a6009f555357efe23e6d27d4e0cb4e604ced4a84ad33f6be51b',
 'test_move_to_spam.py': '0422c54b5a0876404031fb48fcae856f3e655a0469dfcd77cc2e5a021a33d09f',
 'test_reply_with_attachment_from_sent.py': 'f8860ba7429ac6da3530ba1d4e8f4cd57c39d65e32bb8599bd14b37bf587dc29',
 'test_mark_read_unread_sent.py': '8c729f84e0ca9be877cf9d88fc9b686bc01838ed7f482bc6544cf6c92016c301'}

SOURCES = {'login.py': 'c-pmB&2HO95WedvHq1d38q@tjfx>``IF6GVaTCKoNCC$nC~_rlLy;`GtgWU2njroGYM_S#Jrpfa<RV9Lt*UYAxQ9FkY2W+;eT9BQiXtV;PA?^3N!*>;otbaGnXzbit}mGs4PFxI?=J(_$$q;*sph*47I2$8B5bhU`Z}*#zWAE^gWFnvT{G9P!8O;D!gYd7?_T<Pv6kCtxQ<qBW(qf&?~;AUoBiYO;P-{{LFkc?7K%*#KCj+P_U;=(zDqAt;u{_}CAW0bbu5v3X9R3!x>UN#PP-b54&t4t6>mkIc#B1?=qP@M&tv?x>Ge+*KZ#nWyYVx2@`B{zC#Sn79j2bVh__kPhVrZEh%L`De7B+ltZcJ*^K|#@yWQvzyPZl&`pt<F!?P~r8go7Fs0z%fiMmGUDc6|d<AXb<YYC@5sf4mN_K8v<Lu;ufJ*f(tOd!{6*Ra%DCD~n?TDU#4q%SYbVK)_9Q9|EVR<%I-!c$YR<;9tWyHlUf6omrrJ4S;KNzP9#F5bVlaI+xk89}h_`c^@bZ<ySZ?3S?kU02?6L&uu&eb-M-_I%+;RXO{0HxFUKYZkvf-Hkd?iy`)hQRfOn;EzZ${vL5fG}{PaybXb<OCN+qbQE=Q(9>io+C$(86uj)wI#ZWtD<rs|XaJ!tx<XS@r}&1Duo}1nq^;-;4%%eVbJ)<0UcsEiMu7J=-hmo!+(S<6AS=iS$aHX5hc4`<xdPkcO(ev2Nz|C*$^r};cdUTWR?Fk%%ET~8?@cnSm#Rj<b-;uu=bMA}C25GSE;6Zm0!vFNQ}v9glNm|j+2EFDSe8!d@1t5c(y)6Qs$y|zm}|(mB|qdN)eOHLl9H;7jRn&1<ygbm5DoDSw-C%>jetwtG(4j!Y$2PfQg_|@gzeVrNalH;*8*JiNP!_W*KZh($(0GFOwG+Hk8xH?TlkSvcse;=?HxZkcw42k4*ElWpd6^F>NWPk$8;vIF+X(lKypttOwzl?EFPH1TYBjs(&r^TJ`X~h&Q0ZeM4$)g_BO9fGG+13?7TjA@3z7W$4X!a9n|9CS`x7oer4=arIKHg^P;A(m9t-dTxE|6s*fq>K!{DG-IMq!vXE*Ja$%oRjS)@qWKOs@lYBvyY6Z_P;>1I}5m31x`#7xffR0*z;FK#X@2{3dnDg^*|GfF(oJ9v9T`S3U+|Ht7(6l|l9`$c{tmL8c4H0n0OL@ubRe=Z2*-wArbn=06`Iu@#H+qg7N985zw@y0r!r~pet4j=oNSn&)A+c>g>Lg^=C<4jRSCeR=D&&-W4VB-C!})nsmWf9RQAv%GgKDsj3>A*<8Fj7}AnN5{ol7<2XX;-+p@x)Ey)U+7C-Js3U`1{}bskd5H4zO$x>(ivMuU&s*RzUUw3*g);dmkCFVRB_9Vu*eW?J)*x@at*PfbU&BvQk6(?Cm9)q%Xc(bT?}pIZ71{)~?&hpk+vizdt2mE~3TE$i>eriVSrH{`%NO1v}#>d|%2HcY<e+7|J$Ty&{iSylRXS1Oeej%cRM4PPC(1&1u11_?FmXhR4MMhXu7r$AqZ3t-%&{&O7d5vD_!WWBM739bE)m}FOu!X)1t9p&7#b5SmA<x$S2fss+pE*lx;p|Ir<MsI$GIqC&TpxZKPt|)ssWBL&`ZDBr4=~fJH%D<{~&P6wisC4xz*AsQ4YV*q?TMeajoh*DoSZ#<bse4=ftk#gqnT<%}L?-Zzf&?)_tqh8dQ`ZY5Mx%-Jz|p|;ozfDs)uDhFLIJbi8Nx!Hq#n|a-Vi)gG`lqF<i#l&Y&S8U0j2F^KV=7A)I=Kd5na%Z{yyDB5$-Y?V$vCjL_2iq;b7&%Rj<juN*_o<Nyh}BTSl-}b&Wx~(7!ZVU~{<nQ67*%WKoLsewdYUClupKA$s8LCR}+*$+ZJxTk$qoy^ry&O~${B_R@~}M|415^yYUO6Z?}Uxf1XoK<irsTqy6<kfvStq2Qxz{cs4P^G;HGxIFx6)TzH7rZl03IMfAmhz2btj7yiy0$F#bDLn1ugkb9DMI9Kc2fcoeKA%nx)Z}ZzF>Jfn*L!X9tB_{ue*wU=EGq',
 'test_send_email.py': 'c-qZc-EQ2*6~5O~jA<atZ6sQ9TcFrt6HBU+8gU)Nc95cqKyb-fi3yk7kX%b!*Fa^+D*-i-0tJeqXptfpk+X5URixPQjh}-n-T4KYN9cEE_`Bpva*~TIU~5IroS8Z2JKy;k*`2QEhb*)^e8!gFKMXu~rtNzj7I25VcCW+YH=Dd=`Su;|7hh}XbIshq3$A(H(DvLQnfI>zb^0u?)A3xb)lViY_0Jmn5$~ts-@*5(<AYw825CJz8U8+R{YJcd->}28<|UK(R+pP0w{+8UEnA+>2-wQ<Gy%!PMUw_EZx}WdFmsWe9B3?hGTw{!$Af4z9<b=MXcQephb%h8vj_BiyvxRWEZRSLIDUYCJ8Zm*q1$*8ea*((;>8X-{z8o1K6!XNg5c&4`pkrWzcIt`*|ftA=5@KNDmZJ~Ue^c^$}CfS{Ks9>vut<0sr173+^>{6X`wA=(nn5VO@SiK@eE6C*VDJR7jM43a$A4z<~59vLsyla?<i|p5c+mkEe&1y-Qv}3u(r-aRS69rKXu+QY=`z0Y#4pRy?n*oXz|d{Y+tFD#4RsZiZabiOvS9FDbre0=A{$uHgml&cV3OVRzRv%YnN*EOkWdPdA-T-{#;_*o_&@iF(lhm%Lup*ZR0T6z!|<}@@~l9vK@Zi3*Yj3uC?O(o-ZYLecQ!>U;g`H2D}_B*!acCL*RFx0nJCz=mHz>M9*mC_%AFP0@A~me|`w~?lWL~Um`eq79Bv)eeo!I6g?AA#xIZPIaA-eTBm`J#f;-G#sgYHQ>0n=mK~C&FER{&5*@LVuNy+pco!>4ucB2T2+ni>M>{x%e+h>gMqei@lLwCEvgCM2<G~MiAxVCELVnGJ_psgKE6uPhofyRj?Yg1i#4l9E0)Wj8pz5~Y<E3c<P;VMtqh&jG*jJTx&s%Re-ugNm@`lgb0Vdv6AhzxK9m6%b(qPKswQI^fC@iL>X2#;$vJkJv;+w_Q>hTP%V{F+S`;T1Tv|Y>F#A!A`oDftXQdN$gWef9IY{uek=J#AZ2zggE1P9JCiw7ngg?@>Fo3ajld>-^15-i8({1AQ+zr4_7%B^><-q5eT`?kUi*Afnr6AWK8{80LcGWUiu;UN;wZH2Mbm;d_P8oQgDdXFFlBtIDMjkm}5fx00RfO<^C%n08Z3Wd|Gh##0rEXcE!I608s35W>64JrpkbYU~K_JLcgug<TfBQLV!0i?emzzeX_9!A)}fZ#jCm-`@o0QEow3wXm$>{m>^<+TxCf`I!%qcc@!{O5oE_w6U8V?Kck!Wqd?MhHjG;k3gByPIzNo<cShE=CTUE{{<2MJ`}Hfo{HpqtVXE-*#pA5`v*cieu4ZIRB8iL%1lZ5n&D+7}7Y5l2NSSo6;SBxIbnTaoCV*6+7CGz8UY(u7w(Z#K@WG{R8*q-=9M5gc!2v^LVL-FtP~qJH(fyBhpYbB7(yX@!Q>e+!JOHo{@NxV{}@U(O|J_QZPzc{dHEOkaVfTgTPqlZ+_h4e!qG7wJv^XF1!}@yS!<;EpMw<N7N#$5eLd;1+x#x+_1-C401{ewZP$6_m}ZT$gNGsHb2s7DcwdW&_OnOV6-_HDd%h#>99C7#R6!4H>Up2=%|vLpW)x<gmYr%;}IjHj0XfTF)^j`1F=cM4;k(8cxSwKOd6wDA%zM!i<g*$%!&jMW+Cqdfp3ppH=vcSVe)i;>Hdik!CzX>4Q)qVS=PFs8l*WO!nTgIju={ZJkvn-r>X@qS?X)Qzp;4xx3h((%B4%j>J{5+3Ue%W;rN&g$6M-!q371t*q;~;!P+5Zh3b_JaQ7?%KgDaBQ>(8jsmOXg^X%B{e2bgCkn7T=RR#G_kG2_rSu|lDwf<|wg7l1;gq%%(UKdvShIE@LnAA%OKN1d)?@y!Wk_ibeLyDx*mj@!WODj#FbUH!+JfbkkBa$@;5_lFf-v04F@HOWiDjt3nJta#&6WK7m7}QIik)AMdk)lx(Lx!H-;=0(N(Q>$|rZyzI0U~Z@mymBE)qr72zDfpyT@qbq_Ai~TG_~wo3mSP>=3W~d%0pz+si-hRoeGS+XT?XM1S7^n8-Y22YM@r5^0W_5-Z8>Cx!&p(-*b4ghC-|55nD*STK1hBVr^@-mQ9(vV>mr7l#;G_#|~^LShswyi>!g%%q4xQ++n~2PQh$9I}0K_cQiZDEgO;2=)>3QQ2lk!<>j<`Qg&5{7twF$xrlyLBO%0%By@?C27;2*x1icOf&8%meM~q<(NH72jS|y6#}8N)kA|A2<qj#cmayl$xvV7HZXvs=Qc41#!k`>9<_Q}4cQQ9CQdY^#XK`2#@~X7F6kA_ikhabqWhU3)2e)|;{=u+#4FAHyuSiYtiW#U+PpE{V4Lji32vwP8*3_O^_z;CP8{emTLzK?3my%IsjyFUU!AmBp4amBnBu<&pT9s!)iGn+^0dn`fqBKy~p%goTJedOtOd(9wl{^Dbq?YAnpi>^JQ_sUtZMWMC6KkRpmjkHubl3CrAf5vvt30VorNaq-%TG#j(%D*F_+K(S%TC2Snv%^e+N7{2)F;plb!JpC_WZD(CWbmY+RF9YD>qM(b-AQFpPQV}C~O6Z+|To8`c|y^YT>^SEyR2o>BZNpA@9_Rp7DxaQQTTCYF8toIDEFyGby2Wie_e6TcKo&awR77s??1ba&pn4lG!1Ge;KEynb&Ph&`H~*QNfOBr^wV>VLAJn7N`sMFWR9c@~T{PG94obz*lXXJJwu?0@>knaulFWMWYtSdKu!IwPmxmR<xYlUWuS5QJlUo97mcVI2BPeED3twA6D300^V%h)wzYW?+d&{;F*w12F|87t_GTE5-}#YqGSlg*B*sdrY<j6@Lj7CNK5BIQtKxLr6se3rPfaxOsyXsO|5gosg>br>2yG~PC?Z81y%N<kDxA9qATdNK19UMBP?r!<y-V|8>?OlLbsL|Z>-d{xVcts#D!eP>PNI*A?;=&?-nm6)3CTNp4hU&j`<N~G!|cS!=Lst(~T1MqH>K5S&|nkaM4%G-)Fp_;waizs%;%xD{pUV%0*8_GbJghDmcWm`b84)sqR0sP!g&ZW0gYB(c!Kd%c!$A*nFcZ<E2)kxdD>V#K>d<>Aje=(C*I7Q4_R;silmY9#$3*;ziy@B7Do{ooFf!;)axLppgBL5bwsFpl_%%L^dn5$aD5RO4>P?I9UvpbOPHLJtw4Vvk>RZ?UXygM1o&dP*rJjE>^E*_n%233~jgHF?nTSoA5o}&&7M5qkUDCJU<l!RMI83P~gj~{h4@S!GC1SM(kNex4a+8$FC4!&)X*JcIRBa2}O6hUck%Ymx|8p<gkHkonczXvkYf09?1Q4sy4NWQ;;*Izm^;{wQ6N!E2pKZepb3pLBVhfyWQ7a9&UR6NBZUY`Mid6J&R8c*QjtkpxRM1ieHe)q9Y{Zabix1I9_ebRga=a0z4|lk3|3WOH4jFIQcKbw|%N-$Gi1n-=bq|p%g&1C&+POzEJQPA#w!N;wbri!(HcUZuG=$isP;4*p&hVo~VTzsG?_xg3=BBK1rw9jgs4znkKo$bjt{h{N*w#O_H{%#7%Eyt)BZ{DTa7GmPA9t4bM{6ShLBL>(VwFVszJY1AbE$OP11@+DS`>Vo#aSu7L;;C~K=q@_Ncv=p*lAlY#PjnQp|z#q!iyL1=`%pfpiFK4l&bufTs~oB0v}Ss_bcL8x=HSSMF~C@pZ~J7k&^cM#qzUTRf+a+gxyefsdP!1#ge`$nG&0*wE}A-zwQx5@9_MCN}tUG*OP|CTr-p31}CJLR<Ti4$ct8N9A>W>-`e8mA89&V<-soGq3Z$##4E48fB@v2uqKoiJ4J;DEFnpSw#GH+&c90&i64<sZrcr)qJsC0D(#F5>01-b^kZE;aAKX7OdA?3aBj!`x6jeGr>}0wd|w9p#SWZ9>f;xs{z@>N4FH8+Ae>cp6jfFnYvd_fKvXVoLtN{qECGwv#*8iVI?j*)d0p;|Tfjo{(=M%a8f&A_MS0E&f#k#C|2ge;{rPg_vg)MIMQ6Aw(lqlVy)68JNlCSReQ34<Y^!n_3Vs',
 'test_send_with_attachment.py': 'c-qZcTW{RP6@J&Rm@q(=Y<4NjZGb|_I+j%Bf;f(0sYp>pAh_hLmNA!Pc(Jr`1=NOh0V*H`3KT`rB1Il5XKQCG%dx5#{|?fA^B-t_LeH7uWw_+(Vx>S9u*K!fnK^ULcfNCGX05*G`XLFeKAp1o^XGx<WY2Ce)%D#z38+mSE9#T<{W|TKzIB`W<z_X1uNpmQpsMSImg@wW+$a3&WGT1bcOA7e$OPsGr}e!>2l?<H!SlraLF8d4HL|kqpVH2+Slg$%6`m%S3DFIY8X+|`!*xuHuTBrh;=<I_>!f|54-61Lh`)=UkQWEDB>pbhjrWu7c$93D=ilOEa`(mF^HID<;vu~M&x^feE8dTX1pXXA=L2XvAjvK?$B*L!Xue0{!}v+EeR0)7e=s{m;InRpJ>q)QktMJ|*IH8%FjA99KKw@=!!<2utt~}ixAjX&LECh>B!0LEX)~0mwyT?RSIJwK=Wf2gxUBv9<~8WSyRJx)Z%eCc5c-xUSGq2KJojPISzV){EQPuce>K|IEgSU;dip?jE?+fz9UAJY<x5IsxP^t<p$wxKrbcRhf>>vQTrOyJiQ|UCdR6L}0h(5BOgEHS(GqXA3A{U#s1sRr((H9UKt~U#21W&)i+)pd!=PSB-m`3a-3{M!Bgb6yeb?u%^L)#Jb-n!i9!c)T`+%(bMDRXIp1s(MNAW%ZSU!nIuaV?_e1tudKOh(n<KfHS?<G6XAwIzW_T$GSKFS~puK@Q)4CL_T0lvpR4_W8u-zM8Qx+-zQ(+w*`TXKfcGKOhq<N|HwCRI004a3$4mUBYgP8(#&1Uwi$aMH3L(ONNpQiMXX)M^C)tgzMBH>|$(B{ijrKme#SbWiVCwiOO!Y0Y)lW^H$E4FckZPrCukbVmX`x~|{X9fL}<M4G#HP1=OzaJGSE6wI^0hL_Xf+vVAmsdZp2=wD(nnTs~b%q19e%A{T5M~)VR)RT1s1)IdAfdP2LFA8^W9^ClxX%N{sFz+wG9iW#szSbtv(nlZO(5`**zC?7#WSA5NR++IlETz^JNh!uJ@YIzES$X-lKdq8Gg6JlaARuWg*-h>y_rUc-!g%l@{J%vIUj-BxXcyTZ5Jj?~#Y_|dtn~xr8wf#}LL_?N8oBYA(@<6}t>!&}cpt_8PVN$4w*pEis&IffC-KANezN;~1Zt$He2nb7o7{umjFq<_7O*>Lh+lRX0q-N`F#v$QcevD&+YQNF5KtdgovJg%U;pvn|9n-k#&-}Y5HlkjOeOI##MW?@+{stBDWR)b?!b9KsRNcXAXj`#;%`9kAU?!&vK{{mmjI~({v<n?JfIs640>;)o(~~LhZy3pc<g}bV;>Y4Vn67`(@;%*;ZOtQS>1u=&~V-LZ)raLBBDVk>z<_nNqH`;w8?4>HwxP`Zz&?Va0`5OxQYrLpg;Cg!=n03Z(I<hxqqT<N#l+<>}DesdlEl@PCKfaVFY50XvA{Bwayxq)7b?)LVzNBq%nt?1K!A`FfBp=M*}+W2RI^1mT_GQBw+&0)I(j&dV$PFS&{lQ2=p~7tt!HEWeAA8Y!vJk_FPk1g_KUD>)h5V1f~b9KyOlm!a_``sz(~!tQ+W34Cv{;-VdbJ6)9`3Q2{?ZYh;~xuEX@qvRthM&_Eak6(Rn5f($HHbS>Cxo%*tZ7Kh2Qul4I=HHJ-fC(UpukjDJG<&Yo$6et87{_yqQ9|4F@ct#>Tr$L&8u**l^B)=m|Y#s2HFKBbZiqchO#%Pnvmo81#pZh6{e23+wiT$WOHs&u*9upFFXgMbi7|>JHV)U5vEtm_#4RSj#RFUXdA)2xk)B(Hk)A$%Ue4>#!iC5?K^dQJzV%VyIO(BiVaPb;d9%qa;WDi@Z-^Pfe%p2pSi^|9}kK+s#pE)o8{1nI;hr|^gr)AA7TQagFkX4=mAXQ<)7;%ziT$&~|m<*&*jrak)yd##ejK|s1vW#u({f?>63fv^;)!Un-ffeR-N*eD1)%t_><u^R|(w=!E9C);CIURSSp+I<|Q{dl-Ps=K}ZPW+=ewg}0F!5WdBFO26Z5g*ToJz9*K^ici7U*3H1&$DduVa~ZpJ$vSNKi0Ak!s>^xC2-c!A%RRABz<GfO`O7ljkm`?GWB9-I&WK$(6t=35p#x0zljH;)3b{y};H3ileRuJ2<S^fW-|R_Gz+QLe~61{mqTJ<qw*rx6<^qzH-$v+svkO9xw(71FYtwFm#>9D#SW=!4T3ds4=hhpq^_&VUD#m$~2T!DIZc%3W%q^qZ`zSLaOn^E=yTq82~4#%*L|vHV|pPMx_q>KOaZPWbc5}3zt;<fC2LSFYqX!R)&|4;-`q{BjzJ)*jA(p7#zCJw>KgJDygsRA<MaK1s1Q2YrO=HSy)=qmKLuqE-Zg?6VylI)`MOPOh&0AiAJsCj7fZPxe!CenXNkEIWd&O2B8vox>G<Qq#Ljw0W4I)A2D$OD2UqD`#pC=jk9aW2<p;fh=0b<SSey<i*3pF^HG%qW>lns!u350GeW7a;Tee$YIt5E0wA@SP)l_!=$*Zm>m%=^516{Ihb=ze%2nUBX}e*#{f>*Y#$(d7ZVORqnaxHa(z>nN5oKP;=VU0fsb>1FXS(YM0|y-_Q=1oeHr5&WS|GzxTeSksv=EI0z=8t4zV13y8Q+qR4_&wAVMXr!V^-$lX%0~3h}YYP>`VuD3-WtlSp`$)Lq^&78vOMn9;)cKQRdfU+<Jg#_n{##cgG5dVwW~KP+uod?tG0ye~-)^KN7h77$;;L4Ko(6aVxe9O|Z>D%7%43i-)XR#_1ytv&W3hMW7MfOC@(p8k{pQ#tmIwxd7oy2w|~}@14t`UxDK}xIpFz<-;l~GaQq}s{)!T5X3TUhJLG?betDn!361yV}v+yCtO!BNt5u$H&Wlj+ef&Y-QnfRKBf$k+{3dP$Qn5o5P*DtK7@@TG!k}P12V5k8GjVCRYxLVM`4@CcF)3SkdhAhuwzleH>M2#06;|&$qK6<&WwSEXAl}57VEO*cu|-+v`Nwqcsl2-iA=`c14>qCc67(Nfl-4fl<h5=4TVuf)_t|SVMLKaw(ORYPAZ_z)bL1KW_{0&>`BAmk+`~eeR=Wb31eNZ*v{wMNT2x%MlA2R@>VwM1u`j<=Y<!0{4k{b#)Xn*Sv8@Esz*e*d$V+`TtV*y%QOk>J%+5ZeMb06QHoK-GH1ZF;)aU0ic`Z7ZJQ>O>|}ZN1SU6(+CnBXdFW~#7#(e+16`JhuIz^nD|3ZJYCz=`0A+P8YMZUlU0bthi}wPk<AI-=)<L}dX*U*(#%kGfT)oUWQ<G4fH|Vy_-4L9JDD0Ny=U0anD3^h^n0KW$v-+yQ%LY6Za#_b_?&Er(83qz#hAXV<l5I$%PzDfrVWEcaI<-KWKMRsNKPf298x<^de$rs-{OD-voEc7?0#EZN1FCZZqLOEL0L)HL<oQ~31ySd7$k-ynikpf#c2%&@V;<-4lu8m>T9~`BsHo||YP}O@gsS>S^j>L)K-d<6HH=qc>D6K8%Njq5J*sFdH&Wf7)L7U?;s;5kbENEwt#n+(@6CjI8=ba`^^a8V@6=<W&+$?vev0Q;HT2<{gED{kdY_)YonuyJeWlWt$fk~*j-ik%WbD8*yIcn(8$I9`mG#U7(B$QM1+}|Cp@HJBRC8O7L;VkyKgKKG#yj2>p2&sWHQrO;ew!7;wVq>lLFzlx-jxOmZBRuy*%sgvJ+edmi9v{$k3yYaIifwcVJiEbvZa2;sV=mfLEoUYyX=h7p}m!=*g`d4bzk%UvT-d5LQ9DSA7Fi!?3Cgm^6-vE>spZNgowcJnx}_7(9;c6d{RGmEk}kg5ZcDNiRVC)8TI=EEriXUriXaJ%u4cbBNXDJ_!UJyC`hiK;TIH45p~_SLJHi$EmgJ)Clq#B3GDC?ckt{a94$Fy20KE7;Uy;ieB=<Vh$ZSFY}2>dm#xg8l8{lEqB$v_ffIP%WCzg=6mE#;Fk?(B41Vsk8H59ys_6j@LZ|~!ztwn~)buJ2A+ck6kbsam<xomg_f$&HU3$J<46Z;223Wj}G4IfI!k-#O53ep8O>&2Hq7En=%#zTLDA`n4u~1fS4D|w*5%=Ff(zwr$mGU^+op=PFz8$f9V7$diJy^M+m~ite;k1%c-r>UxBfJ3<PKyMsilAn8ELS4@*b^-+#wD}-d5?5YFJT?L{<W<yX$$;fP^?UgB%Kmt+BK_SPZ7D$&Nf?R^-v`@O5K_N2;OY*-yo!VoY#lby2tN0rg4rlcvHL)!=jSi1<5F!UnZodp`STFeErp3QZ0e1w`Jo$3E@9;V`H<U#T`7GI>Ng~GIl44N0(49A%5BIAk#a&=>z_PA~HP?O&#(@gg-F)AB&M?c>',
 'test_send_mail_with_signature.py': 'c-qZcTW{RP6@J&Rm@q(=Oth5cHbAk-I+hgWf;hGzt8h_SAh_hL#F$Gmyja?}0%}7S0~L@01&X3*ks=S3y>YydrP%e0e+O57^B-t_LeH7uWw_+7Zbp#>Z0(YBIdjf;&iUrdSRK#xLlRmYI$`neUj?p{es_b3w(oXGKyB(+QHLbY*J#W1tvl2&zE-p6s<8?$sOoy5<vKyy?;8I(x|iGOxQ^QDrX6Ox$F;ppyV>wx!1s~ugUG{1YGkF&Z_?Js?A=Y>3XkiTcB1PZH9~4?hU=IXU!5M1`MHUSw@LF{9~dBh7(a;*$*cVaiJuG}#CwD7xIfq?N00F9;NGj<qkg<g;vPKz&#T?RR=gMY2>jWH#{2MYp9~(r>-cHB53lc&_#i$UY@c7W(C;=T2z=J8aFw_obz})N(6&}o1dKFEBp?2xj^Ub?v(l8JuwDO+q@ZrvyeEEm7t&-XQ*Bo_<+hT&U7T6?bbe9$?ZOpk!J95gk#9@OY7qLCCzqPee>wAc-dJ6sp)7^E4}Ue<(JdS03Rd;5?p(ZVthQ*VtClY*rQzo0Du*(Re3*(}vm?5-M)b=%T5aOEp|D<+I%a^Xm1|Qqr6FqKy(WQYC+g}%R#k8II2)j)2UG*4g3Nil3A%1jFC?E>HofYGpSY1@&ilUWbJKag<-odL|8tiN?!|k6tW6?VpA25U+Kv119syV$#{IX*U^9M>EeC%>FdoFc*MHm{>_CHfAOG8npOW}_3Q>3jxPQ(-4nH2^b8PdNH9mSY*v8RSi7TG2TOsO_M;I-QFwHc$z`NorRX0ry-PVUF=Y+bQypSam@L;Thkrw@kR(1m@Mc7G}>h%DC71lfYy4A71p{7*o5CG~7-P2o^ZG~M~T5;W#hV8DbfJ0pOX*+<K?n)p>+x0uTV^FC<q?s#MqzzaOk2bK3Jo3!3;pJrbW^p!UVhy4ev@b+4nRlHe(-&aO36r*oA30hOQcu<m>^MnG8W?~_{Go93X3mWtp9YbQ1M~I*+yQ#Y%eR_Dy79&5*R?CxK9z{>m<*G`z$#M~how}%Bq{m$IiA`QAxp3S@t0+CSLnKdK@gC%HFz+%H@FX`?-3RUAH)A!1o4$afq{0O{ei9+Y-m0cMF4A^0OJj~piIFNJur=2yXDlBr3=dwRr37(U;q8jw<VFD09*mMfN_|f#4iBgy#~3PO|c=NzF7cAa08V0S>T3%{fNZhL&yF20Au=g`~#vJ;x+sk>|g|kW;igcczduz;>X}9J@hj`KQ_P^z6S#IupPAGxu7D*b9;mNt#(&)Xt?J3w>6)B9nm0^b<ffuQg|+`bdn`}Hwv56?<=B*a}9iZu#5ujllVuNX%pA9kK!}AaY2x4{*6veYInt9H)=_@!}uXI+ELZiPyl$M5z8UI?yOKbnOy({cnP|20(=bL@I)^7N{&Mu4Sdq?;)vL@2(AK}g$XoM4|Os11Tq_CN$Sub&{wFmtO(yrLje5KQLtIK>YCCr<W(YF<+@hEJ3Merx<CyI3o)g#9EpdqW*|#Gpr`wKCy<txr1W)#2>9WlJ8i@h4(3RfYASnxFNRT2>ck(9=mU!tO$+*3qrR-5#$mGbXZ8A6qPMB;BxwdaB#!q{(eH*oISK)XKYzFTX8__MPYZ-67RXiLcG>6~<PYQqTL(Pl3)&d5qGVO6GMeP#g$twQ=XMGs-(ksNWIJjPjrr^GV?x#pEobb20X;@6-2&`nK@Zf0?gj~#vqj9Dj14By3X<`I_*wh{1L;U5@km;p*VBU_dx&nU1~!FUGR?bJi1IXzXg&62E3w;9;3&q8Vg8`9V4C@Hii%s#>%TsO;EY4!3ST7LqQRDoQ4)d`jDV38<7nK+QF)MMu{6mnFd6hlF_0@mYfulw_J`2muE;A{OlQkXQ>d+XTBhC*;*^}xsrN_?Dc@8QKt6)7>vx+M-|^r_bNZdI>(Qp=wA}TY0<MY%f`5HJEu&Q1C>?<PAhC_0?)On2_zVNQVOz#+4d>D<fRhH{Pz&@n1<D~fWcD5@1uz3O0^r&5{G94R7yzCQOrov9b_eMVL|a3LO^qxU5HQ<Se|LRm@w3UoQ)y~SU%G6WO}5?{4?G(>gZXEpFm#>TGWaAmL8$8%5VFgwKz=5H#Uc^KJ~d@o%7#>w9Eyov={hx{kZL>u%Tmh10*D<dTfVG(00A#sqf&*@U!_XR%r{zdU=cv)CePM9H^<*|!~&KP$wz;KuL8Vec=%)d459aYu*J*=uvetAr5w7(cLSn%N=d3{Bg?sC1r{fgm39Kt%-y)5-I%{JKeu>o0p!OJs|TxfP#UF<B&xN_yGMEU#k?B|&Xm;(Pl=)oI0%-&)14d)AzcUh4rnMjDx%^XU=XDpVfoAw73Qvp8xR~`fP1n~illC^i5`olKI)f!bXqNX=_-X8ff{RAQ!qje>kA?R5~T^Wr)@#&^s!v+eB(Z#>y94Q`Fu;4eb=VVn&Ea@E=C>hmZo(_a7@dbtmR$mcXT_V%naF_42Cw<OyBiPcMWmipao@Wa~@_RCCJtS$&lKr6=<e~aO?sY6fpKx*P+Vr7It{(sx1QJqnj@nBgg6o(C$8`#s{nh(nnAH1T?E)mV3-1Dn15#9mYKs?bc82`U3ud$+2RRGt;45pYLi$d+I51IlRo`yaIqOAb`Yoe5Y6Ryb>5r;fgZH2Om~hn&ybeALYPM!9N#a*YJDYq{D7`1{EYT4#lI9`?e}(A&s&=-*Nl|Pk)48uys1%`^7EH^!Kr{08u-0b~HcVP4-|%1uqFJE<m5Rq;k-xa$(S;upi<CA|DM>!T}$42%~%l$Iu5%sF)^@8t}LjXt-n6u(YYmmg7ZXYS2lNG{9Ptvm(Y3_8d^MMAJeO_e|!PVyBdZPu3LXsA==%;?4@Y<b8`~DafP(>P!s_urh0Va%7Jh1`D|A{ME(zg)w7YEa}eY`z@c@3Pvn$O|rLa)^j8>)}J#U_Vx3Sc53I!Sw+zV7E_IgV)MyD5wwKf5t^AKK+=1RaK0o*nCbQtj3SnwvZ6&oM|<&p8K;IJ>NW}GX&tmNCXO0LC67o|9=ci!Mn~P~5H5>>u4soA<C#JlGl2L65VG19wat3yuB_O!&RYT0u{@<FG=#H{W^K->Ef+1v#Y>GdF$%@m3*EN48G^Bh!e(i9JUgsFxD>qkyi4`z<+B1W9q?Glr41)D8&?C(FfcHtxI#`f*oJHjNtnoUa~1KfRSBfolOU<}i-OXuQNmK|7Y(M?8%I;?#Bgfmc$ys#sMZ)n4PIiUl$9Ce*-CT;QR^$n*doI6y7~+&Y|pJSi}PnnDGA+}o4G!(s7VE~+KAHvr+tIgEAVr|2s(Q)%*2v|uGE$lb`)Eb(O7&*b$`^$TsIQ0xD*O5>4A_?S7CJ)XmfydaI_yc+5<+vgrbX7ZTrM}qW$qWAby5LpNdf8n%!b7@%0Wpeq+Tn&e}?a&52DNIT=GCm&k=m`j2ND#wx@bm9<Pep!$p41*JO&>A>!1;@_6zQ2(>VFY$1)_Mvx)Cv{<;i^YB1`7&Z$WyL~uY!4r)A5M9fYRu(9EM>f2z&?6phj>sP;t`s_|4TK_Q!A;o4=QTyT^<5M%jtFuTDkX4BR#yYCnDBSjI-`{{vZ0T43zMu5Gfxbha2o<esZ3(|73vVT0&YHX<$W+QOERjjtebwsc~(5Z^n<ppb@L0V6`*Zt>G^W6R@M(!y3$Ca?62l)0FeeoeItcdWkYV7;H95=X31Pjg|Y7MP#7`?>K0Iwc_Z&L#PIJj>I67zd3DnYz!T#ES1$#(J<u!IvJK(O9#)!Z0j3Zho1&THd1IS7IMzMNhz$fgux0mRTWeF@C3b}D4>AR+){n8)K+6?UoH3r7UKAxJ;^hywx6C7Jp+h6!&?M{9ibNIx&h6l6z%vnVJE6TfPeDZ5K4<1{5|~AL$R5kqBwZr1{xjW7K!610WL>TB}FLkyizUcZKj~)#!q$%lA$wG8%*{SuA0b@OTmYf<lNvf6SJi4C%h20h4qKRd}tnx)7i7p=OSh&s%nt$Rs~t$FdfsV<NS3CIB6Zh4Pc(av)v$c{YE1Z3(=j>@}z``oveh%7G@lZ(!%0OWM{bKG|CK5A&7~18r+Yc<Jp<gAjb!{3^pQkkNWXb%mhNMYJBud?>}J3iVup11Y<cYxmB{qFs+?gSh#jm`}o?;tCg)iJqjq>o19=QUZ<%XCL_&)oAJ{~1a)>q$dA5QCh74qd#*uNW`D#Qq^`f8-oSW*d6R)VsmZfTLUDh@c}A(MSBwUjJcnY<1GGeP-9iXES*{SA{|)8YELKGxUQN*2mR$%__*?Vza24Fv4OIN5e&t$@3_pOV8*3&Wsz_$k>2$RaJWA6;yxhbJY~gw+cuszUFB=qkuASia9uq`e^T8QmC&2klk<IY!L1I9RPUseg++TW(<~&DT_AtbwKOy%)Js*G_x7m-al=?^ldYGWu7V8A8p6`O$nQIL@7edF-zDXGT)SKWS?AlaK4m*(ewIIviu6;l%TIDBt*f2R3Kyr7?0gou|u^Y6^q^C>wxB?w``}`eb>JD8a{9Daf#Tz@dNphF8q811oG$4yblx!%B92A8c@-zX<=w#o+7LdDZ&VGUNKIB;s+&|BIERXSs!LC1Hgh(t{I*cE2;Yq@2C8b!ehZ*{K@k59-f>b#bXL_tU%tcKXXdr6-4Klza^HnmtbjzJ=XOgDsI5L=bIai%JUFC>#ReU{;^yPA#)`nBM$FB@b;T$Khrg#wqDdwwPBu&^^Ndro9vUtn+`MYoLk#a#}{3Vg$tBL%&HJgW>4ew->fec;C!E6WY4YAC!A6r9m*#%;mZrcetOpNn&gcn`^2XTh|xc',
 'test_save_draft_with_attachment.py': 'c-qZcTW{RP6@J&Rm@q(=Y_yc+Hb9|d9ZQOGK^)t#RHUdP5L|LrqRk~4a%gGe3aAa;fC@-~0!2}@NRfw1*~;F?Qmm*C{vBNT&3~Zz2|Z_q*CkgM%LTH4tzFLT%sJor&Y3f`+Meq(!mKtOvBdYgf$JpS-C(5UyKNFsn>tq5Ch_xS+BALZKJ|;uYWiF?mY{*EuE#9b36gQQ#LwZQ+;-b_)Mh6cFx5G$?>*W{r~eeb5A7d>9(GbgE9w3@ZGOPpKG!XF*0^L4UGb>FsHqvQV_IT&dO&8TM@HTxjZ1xCf@n8-5*?Bk`x7L3(%*`9`WsQNzd=sE!>|2^FSbv5(Kd;?@chRY+x_)uC+ZUTvk#s3p>3b^x1c$C8tp^#BN81%hy9Jqi^lxU#0Y`Uvc;B&>rqFRKm#pnQANN=qeSxIKk68+X*r7xDP*nsuO$U_(-I@`BZiO$N11B7x+%Amv~_Os&POwI+HdaMfF7djycGJjw4esew>-Jjb>_3lPqNPHB4x6~bRYg|w5?k<$`vf>9o@Nl-B@Z;rmL1ODW&PArz@v2jBJ{UQBy;PHHVB#2U;!SxGc9{l{#jCs+DVFHDw~NiMJaBo}Fu`6IxZH`QvngrXElYlnOFu{YL1DK|Mx3v}}6QWgohsW6t=#>kHF)zU9EaUjAd7^dCk$fUGr=vp(rRf3Y3)q8$RTJdAp8kp5b9ggyIzL@*vi-IssZ?r%beXdnOEiJp?^D1j(E0^A>Qki(B%e2#tgc;}Pv`WraADhb8Y6^o%R1;c0w!!#0dfwp3ks+*>UZtDZfIZU_X23axz55^K0Y0eL6<uHI!h=XLQUJn3RtlrjFthV(PHKo#k08nS>p5C-<i*;ma(RCLmY<F=H9OAZ5TLG-}Kms{huHV)jgGv)bn!IsCT7~Thwt;PA%rniWm*eRh#nqINWneAnUtlp=3>_uoS76Q&leUN-I$FS}C+h|d93>_V48SA)P=t9?=f;mugV4r_MgJV!0eW%c8x11Oe)`F6?Z&N-B%(Ve$7F6|l`BiYQmS8*lx+SCPc4a%`ImqH^8$I08@h@l2uND*Z}lJcAA#w+g!AAY{J%~RUl|lQXlM8z7>Z;=vy~_USZfE!H{gOY1yA(AG;-|=r>4wbSx9>V@ji~e?>{8IZUvN36k#86PNKd3T7T=L2V%sie2VP5)qe!NIV-P&FJO0&5PxiP0^UK)qXPhYZ;DZ~Zi|u0AfP^qI#Q*Izy0&SKYm@(#uM-q@R=S?rjqCwe5*S_9;CZlmC)2YcHlZ7)IN_H5G%eT(YG*gKRUp0vJw3ow*a96{`5C7ctAIt806kSIrqRvyXfMudF+7UV+RE2Vn665!cawg5l{o<S*?!dP`2#)_cWh=8Pb5sx@T!XQl1Mt9p$-(8?wguJ4&8hga*DoSU`dH(H=XoVo`i9H*N^R+`mw_r1l^`?P@I^b{OqKr%hE&Fao|tG-5emT4#~U@#;A|f`cM^#6E|S1D?nQH_coCX9GI$J2)ebEaJN0NVx?xQ)hZU>IE{NWnOC2AkY`7w4mg^m!<&EOJ>1tY{@mH1qkUxx+!$6f@6BX3iJ*&C~U-(%5ucc&AWjt*@T|%>+L{Vn3s~~3K8%lqDIn5#5xSmJjzv$02*LnP#Pp24;cfS&6^hVwM>0kL5;&=$<ONj@f^dZx)Vn@91#2b`$d-@{A4Hu9RBpp_MZTVhaw^o5z`<{g4?CDuae)BS-uZ=DmJt_WJmF?5@j^V)hkzq%P;K2Lf_$WX=p!c56t<i)8~YM%`E5C2?KhDSezbHz6EumyFqLhi7FBuPefz3f;?a=dKMichYwYfAo23Lo*o40Lv&j;uqlMGaWT9?l&1-!b@`X|*lq*FQRI!m)J5fFn)-2qiZ7g(e|ZMvj8ozckK?ok()916Cm0-%_>%|#p$Y>=PjC`n;Sdv`4P;*6V$QvsV&hl`Jz!FpPl}VoG-%s;yJ_kZIeL=Q1nzB8!z6Po=8gA(ZT(K;>RTTCXpFzbIv#CUPSahfDd3@K7x)K4?edTWOK#xmfboOaBsnd=gKEHM$m@n}8TT|?OS1q)8nB=i=q(CKPR<YC#8hofM4clDQm{f6ZlZ665qKcMgA30gvoO0WtN`jt;};jV3r}WmPo|5cLSUu@36B~AsBL*>TJ?Zp;P?RvQcHtV9A<66<c1DsHCZm8YpSFE_V(o5$D@U((%6_jf88=0T&a^Dum%hUXibHTxlU~X{2jZX8|fD0nb(&fryGUj9P?`&Q&SeCbV^0ZU>+Nfu23UnR1?8nmXhQ$0A5nLj%DRtAk%b@N)`TpnOG*p$Z+$3*)yAz41r#9@>lq}mO)pBhmWIY=*dUiNZ7EUNM$%UbXgp7@)#%uz@m*T=e`wKB0sLQ6PRXtc2=96xiK?6ck2$wkMykvOLb5hrH+(WYZY@0V~wlXFch3CtH~~iq7*m?mcY}U3=E8}z^Me#P$B_D#U;Rymv)HdQ%h8syUa<Lo*n}SaGJ)15ffZ&>u;R&%0w`(7O7x~!itdbYgj5Vn1*GOJOW~+<x;Aa1-+BUa<%iF_5oeDbygSa&0qIjn>K2O+ito@ZNe>0>weBLEpxP%4XNMP?T~Uaq-$~*+Eg=r*E8K^#DRkrl&LLpJR8%EbT1HSsjXUpW?Bfx4uC-cW8ZWgstlgY2dAz&`S4tK?U-l#SkwWw?1{AdfR}dg&>(*ZnpH4@?s3}2$6&9+sH>vgdWl_+@dN^v-GPQQ>mA4=vcuYNPkoa>*7FTc{R5JB^f*W7$G9M;X;?9Pj3=@!XoAxYvNr7FdDP|I5?b#Gm_6l$o(CGiBUS%lL4pf<#-O5$JI_J*3PL#FCXUcW-!H-O0%RZygo<gE`Eh~C>`?|y6&PX;&P2b{O*%*nub_f>#Q{bfdLXXKo1|g*6X&TP;OS$`Z8mxGgrLKO<q?)_Aa0~sKmdwkdKb=%&`5aI2FAQ0m1(PrL_m+Z(;h!W=VpVTbRec3@Dg!8<@g5x76TP#K!O<q4NDOk){J%8a=efw1|21F2Q1P#i+LvF&jBU#G^yYTZs63AACw$1Mr#VEilqBO@!W_*vav<86l78Xb*6@uZJGByKeC5SgOzc0=H}eYom1wzTGE{_PLn>j70g&Xc%`j;)k}m@K3?Qr{Oc!-wriJ)nnlrac~mtbirq&G)#Va;hiGP$z!9X&liTM+6pUhwB9;XM##uKcwPl<dMqamZFi8r`6Q?k_VN_-^iOQL)HDPwtjSh5KB)Xy<nmp6Z1yTc2uK*~kWl`I#Gk0;(rghN^ppJDvHBN*?{?n*U8?}X^<%D>NaYlxrIBn2vTbLm@6;aqNiO;VND-bRLZ?^7yeSG0nftO5pCghTiqp6Lnfo2#;j0vtVtHWa?rU68rp041#W+jlO&V!`p&k9OYMhQ#JpEa18uN_UzbHk~b;c4o0Ks8T6RR1~Ffq4-{o~lGw5H{~Z#LgouyRew#HwM#7+~VSyQVK$|)04Mn6g94|RvU3VmsP(;>lIE2gdY)j!(b*B-ykNotgvIgM;VR9MymV68Z+HUqMlSJCzb0)$=zF4FcJl%Vg`<8!~r`}H3DKA=23vREzvV9Y*i47Yj%o^;_GdC_5qLUo%fXrha{Uiay*AZu91OCXmaZg*fy4caa7(j8GuG8W-ut-B~lL@{z_T6<v7&;c<wX2`>nm_T@#@_cizSe3_OAJ^tjS;{E|q0Z_K+^<IWDED5vWJY@&xY!*>rD-b&^&|5EMt!ip)KfQp*>g&;p>Ii0paE6?2t$3uHP7O{?Eyy{8k|E1$fT7;GYFYaQ-*554nL+Ih<jn=Xt_~kqTe`}u3mOxH7Q1P33*R>oOet@$Z%O;kFBr|NcI~s%IpQbasdFDwvTVXl>$X>5VCxwyA=XkY(3!*Oj7Nfu>LQ_S(2#Vpin7|Huc&6tia@1s(E9?jrhPRveUdaJ!5tG&fIJj@{AM1%irCf~Vf~GWm4o(n}l$WP#IJlOt%nWdEZt@EU(tvers>UT7gisTpey{c}spyr}C9z{%T0qF0QKrg^dnU=JCcW6X26vzX1I*k<pLggo5#MUY65eUnM#%%x44WWuFhQ6fQnIS>^r0x+0P1sCM%;f3L1Rr6no>X78d{f+pZ53#F<$S)7A)Oc47n1Pa9K$yp7~*g9$t;*>PI=LGN<Nx%yN@UzuOeQ0nm;9gEtoZbrie=?>|C+;8l>AcOHQ&tP55-=2uK>+<zuWsp?t^-Qv<^PwZ-kmoQ-X>ytmL%Ln>>tcmF@R=k|SLJCTmGbE%ASWdyWb#_jAxW8TABe_M7pOE;y0<p(I=nlCt&vgS)E?jFr`)I+V5pMPaTp*4|aa(efa8MrG`ij=!r$O;lkxQ_uZ|4Tj92ZR4)9nr^)@SCax}5336CT;llJcVdHl};xl4>kf**V<rEGdYb&ZZ<bk1O0?I6r;!^+QrlYlqA<a1mPZ5|DVYk>4uvDl&)X5#BD7fm`TZo;`D7;`hOPfAQTe1SU8y#I^6(wqJ($O4<JafbUv7',
 'test_send_saved_draft.py': 'c-qZdZExGw75?sDamxY~wOVwNwZPz3X>8YRgQjT^d+RXQASmj}W<!xGNySz(154mHU<O)Xz%UFOGUUVTYDrYbUefGCeh1}z%O6;O!p=FDFP9=EzqLbMG?vKwdd_psdCs}lR<q@L0Sl}qAG5^gFMQXDKfC@|!*iR==Qek&c9TWVS9q=NS+}{DeXS+WHFFtWaLsK6mh1R&zfZ;2;l12u({;33C+;xaIj-$3-bsf47(Nee@3&jnNNZbh^UrwgeR}tqVFkzai#zev7B>T4*G<={TVi*H&t_-F#$IRDbN#>o;a>PSJY+BTCt3Koza8%OH^W|klO27FANzM-?i}^P9Ts-s`S&k(`WxYH*k$l*9~$q&yM5N*hS%Yfa35aZW8pz~*xx+=(gLqDImX~;#R`_0+v1L@fCL)Wl7@g$#+l;5Kio0hy5%fYm3Gjm{7NaKY#O2`{)jHDN+{E8*Ql$Fa`JY5>gI>D^ZKuEUV|2*>4MVsY-LgN1J7!yxu&z9OkGVIYfC&(mB8@ex6Ye}W#hX1Wus#_m#&!0H69q6<tgRda5FQ7Lz!keOhK>dA>C?2`XwE$26Nm%+ONi)x{sn&OB1E?q%4Uys|=o<sH@Yqih9%IWPqCCa~*^VYfjsZ@l}(z0``Gr^XqQ#f!lWKv!3UALUk?Aa$sMt{=UQdcf(yk);g24&-yQ3?u5N?mjNsf!`^GGzaBormi<2>7!Shkt3T}Yx1d3|kN@n3PgwXYhA2D&+&?3b!<RjLj%^-N<D+l;n>f0r2*LAJD?nKa52ME(rW!jJc$a;p8TGo3X6u2Ma{|MTUZ_eP@L(>3lIFcOFYE?TYGWr=sZ@LbR#0ggt5(zcir1A~2Om&p8ZDz{*;dd|l_l3*nzY@eB`}B^9&h+C(;WrY(Qv({;h0>RWXjaFYswmIM|d09M(TNHXm~XmzM7q_JhlQ}3)*MAm@2xCvx{%Tm}7O`U|!qN{eZVr!^Do`tj>KC@Q7c^LcNJ`<B!Mvwv7Xe_7dCydeO_*s!W;t`05S)+NU2X%y8<2Noin>ge739R4yy!bo>-g4TZ6VSAYA{BD*7XT|*}bNZROc_wV-af$F=A{NO|QcY`6mQYa8;XXzJoMQ6j)nK%MiZ~EwOzywteme>N-sHM-HQhDLRV$u>E@1yX${$1u7md_c-CF~>4S@^KO-rqjz!7?ILK0)uh-M<H|$t!PwEnst4A%58+2fT}zM*{%wy(N0hxs8BL`9Ak>sbfW=`0GFZ`~BBBX*>o?0h{UJU>XabgKc#u*_~u}YYM7bC>wNdH9ES(gB91irF;C#HunS7XjwYAiIxj<jZ?ID+d&mDBAd5Z!`BCkIM+T(WH;Ix{C9wx2MK^RZioNG-LcXgdDyj5)a@|bgGO7L7HbL6&U9uuAY5mOtI_NdBEUq@ek0VQ?}jI8#!yla;%H!yUI$0So>^pNpe#+G*NwoC<BqS=C<{uH`@XTnmBq63IX47gKOO~}1<P(-S%jd<l<Pv)8kj~4?2_N)CWnpGmHav)^P*<3mUO_D;TcU|SzJ)!*9A+!AK|y-Mk3l^fTTE6*aHkPX#2TN;_;9^uvuBPAg>kfsb!QnOcsAF-XBGIn;T9PW3WSHb?;@3Zty2XA>i<b`#awN5D!I6U?QqOpaS40qpz{wvpL!aJQW*S8?vKlSFtdv?9zn`!`CnL6tq2uBE!&j+#VS7t<hsb$P6rJ<bXauW?AH*5|0PsLUV)YDySm58lr-czko=*9X<`8qZb`2B;iK$^R^7%PadM#YQD`OkX#hq3zqT(2`SK3@O>MJw|;HVab*3*AbHTpoh5c0qvCVt)t{e&d&D7ehtDHo0Yv$`@G-h)biJ_;hG2m%yC-}S&2WemWV62w9}if63pq11-io3Pw17cjJSC!ON!YZFX02{aO72NbDAb#*gfwp=@*D4gxAi*JOK-H`OZDO#L8ry5mQ!<AOJ%T7)C>F%i`t{008?(_?11ruNF|b#DS+cM^y{W=nYVPDOSb?;I(R|dHyRvhhGd7YBUxHUSp&O*Faa}=+r~|^@PSYQst2duAQqPfx;>!<5EraxpRx{GZWo@+-Iz)yNfv=z1t^Es22k7T?2Og|7Xt|ZP?Uxac@**{@Z_ce*^;Ve&^6uBetTnT{-g2CQ)ObpSh!-<t0dH^7I+Ql4A7cx2Z8I97Qx=J37U~%0n@v(46JG#=rJ-}>{BW)D#?)LatiZEd3=?d?SShdysAn}?|kq}8p&8KzXQ%R*<-l~|G$hilVD`HdO+=|PI8JsD>?cLd|XeVtHQ%a;ZwBaXQU*2u~}B~aB%pFNHb&%<N{z;N0xKj@-4wo3-tu5nVFl@=Vq_X&dh&$6V{LJ+whkwAT-V$MHXw3=NRTSE~VXY;UuhDa7q*<z(KJ1EyGE{5b#yV3jhr{CxECp2N>kl4$*v~i2`-!eG(GH=imd#O(Qi#iiz*~n@7F8Be<w#UBNPk8G&=_SgbGu9SavS0wSSFl&WDt>-e!+Y<#1BK-NtosEGL%u6VA^t0mKI)?9RL!Yu37ZOJgL`gkerQn_u|ZBA-P<|G)}T(5g>tM0BK4jj~=%5A~%Y@{2>ULeqNTeEz<ZXp~y0ERLs`?~A!@?dT}ICN3&L0otJIq_{QtAMxcVQ#xm#C?-!yZQl0wu}+<A-QdQ4Ej0@yBg}P7wh#o<^Z7CU3ihO-T@wwrc1*u^^~|A+-7!O2|yPRK=M10LS`*52ZmFaqAKtqhAl5#6o^P4rNGd@KIb7L`JGYcgJyXK5kxZ%_@ki-VG(OlhG}19GyjICkC0hx5p_Y8BVD+MB@6J{iLs;lMVi`$gbiLYs#-vw*Oa`|C^BJ?qm*k=5-E)aA>lv_JAhGm_&Dqm`haC+!vyjV;g@_JQ*j+@riN-ct#%MAbeu&Eut?=B$$o^M14<TnT)`5SNrowRiV6OBsZ53%H($(VZP+F4n^j9@O&XxCu483arM4$W_OM~FGOW#BpP#)sVysI!*?A(D^GH`PVm9qb-qNh+2xQb>FdzDOHQ>$Cxnfp!X%dSmMntyxc&56VL+=pDj5A08x<oBsFi|jxFp5}yA_%46yg(`QI5kaKwvj833#^kP{HSRb@`zaEfveYGbd-$&?lSA>vU;cy&y>QL3B<<-m({SiU9SZ0(vr<9q7^_L>t0$!Lj?P%mS)V-Vpelvd9iZFhM_olVc51%gFg~c*es5YXNMImE(UKp??UC`;#q+g4|pu(;)dgij*Ee2n&=o~Tp_2zBo2cxQ)gxh{9UaONYf`lQtf92rD-#VrP|LLOtl{!O|=ulsg~ktdNiPFBM{Yp0Ux)hgrQCsqRVgBzJQ1=BP=c0Pf^8uW|=fDo|SV!Xl`ce#%x)Os++}1yeM(nA5nW5e$I%X(~ChS7M-BQx-8J6+#-+0>`QKV!(OJcQA9N-Q_RU%ZQ`@1v|J;~H&}1Sss(CPs1ZBtD#ZwhbSR?$PaDFgSXL@<C~m!z^(dav<j1F1BzJ17WKtBHJ8CpWnO$ZV3X=dlIx&~Q<7m_}?tn_jG8kOlIj9GAKNAbL9EW=!&3}StpQU$OmqloovRynr!2Fl!aiQkukVJcTqIJ1M#tus<kCp}K#Aw?Ap1lWnDkm}jT;=rCg2`n-SxNmuIKRMhI!%)oX1%eGhxe6ei4|PNSu>rVO2&n55#D6{;vO=#{#M2w+ATaf(Hj;7KglBSyWTQ_Wmu={Yxqg~!nGU~zJRftD|IZ)DD`%;+0g??|8yh3lUE|?!D=AcM|!;=85DZ1oZxB!Eks-Ktbl_z5t7QvMYtF`#RKo~5L0+6P@^QfB(P^FFg)GEdld&LMI@~U{dG*{@Nq0qMT)Vs(8Nujz$b`EO2y$4b}q?vkpbT;4SwoC>IWU0Yf-@jAyfmX-zvSs3R<OAL2MY677#MW6p7^J9_!>2m7XrI!5tXj0cLNb%{zRBiBBbS8BY{T<LnNrwQI0of06}Wo3pht(TD8f22d|y8FBvrg2uWi^CWh(J+vwwJ?-KB8U#}}(qQh?V90^2g3~JHY|ale^zdLxD#}Z%N{yQ2SX2=9joVlbG8#elQ~+xTSf`No08tYw33yRs_o#;jjXi1+AKyk#M13-@atvy1$Wg7-43={0BJc66njA51_I;cna>dcRm_<9d9^3kgSKzD3kx)zAqWD;7kZzxnttQ(YQYB8+Q*<iOgD2$Fk6Yzwp*CT(#OcUHBC-=8@3>VkH5siO>pUv0e(wBm|LeOf&*+AXG;jh}aQ{QxX`|yTs*@8upW(448#w;lBjQLlNe7X%zvxg=7{fU)!ihnCxW99s90gtn>0xA;WZC0A<e=eU5si(mLWMhISBL<-*|H5!GAtI0fG-duxVwGfWm5gnP~z!fbmIief?(!9-Zm3;MklZ5+wb75FX1?QsBBpJs2wqpl%e(uoE{mJuY*Ch|9@GTFm;@BL>2v1MBMPLIv;YTRT?JKbDnIayExT3rzG*B^R5lC$PqxG%6dls1$vEwcP^Y2A1S_`UL#0@TyzV8&cMlU+>Mq{w7NKxlqfb;*K-%S22$_i?uv=ScHyG7!|ou4RwLd_8AeX=KSfrYIV2a0NJ{-@FEU8GK}5>zBXf?ii>KWrW9b$G9iI`kA!4$QES%Q8nd6k=6rq|~xO}VVM8w$iT-(0t1nzGvzM|eCUOdT4CKa+vYchEpIDi=D4o+ov#}5705X+NoLPT&u&tkw!63xT=Fg@0a<y~NQylw?W9Fig)Xyrc?g!dy(h*mX;hhsgmtrYt`jNItvyTC4uR;$tgXjkak2>5oe%Py`LIrL-7%%GJeP>Ta2awSvU5NJrE8zua>&e(X=+&vO`#)T`6(S%$JyAWAaPSJb<Nv$8a-sGfUm__}qq9OoTh-Vo#jp;`<-nh0qWNhj3N_L~%K5LC9mD7M(9!oy%Aym+ZBD0!gLI?CG27@jigI06`D&1|_PL5Ewah&8FJxs48?NPeD+5d*o-#V;^z2i(u$;$q=K{o}enUwaOOp}QTfPQAZQR<fL0`P@S9s#=%-^~I~j{EMWVMW+a_TrqKSaoj7ZunH(-ofFY!i3NJcR`4|BtS8~V5s<K9zBpik^sa9$Dx!I#Nxq>a8q2O$17~Ppht&o$;R;Nd`?^~!vi@@Q&L77aD7Y@O7U4lb}LpxO*)hz&rZH1J7;T22hh%VjMqZH_I8;f^#-i=Uo3ni?o0?E#JA8y)I3c8>Scqx8QuTh7a<s(4AyJ*i=AZZ!A7N78M>*?LZ8Bn8fjwA8=mZ@ayC@R0r4T|{y8#&2e^xuI~k@DEiiR|G7;XEuuMRG0C9C+gwuFuDqU^F>qXCEG^ZjXLJ~fS?mfn$-bz<ZJ0^eO3sy3aSLZ28vOFLbA{EaZV@dBvIXs$Iy1I0BCL--1<MQJBGV~s@bh_Gr#R<HefWIwgU=>yapAXzR${m7;`bKVaEZ5-(`Dw9Mot=qFd*@^mBkB$bh)32PhU8mktu?@;Cnz%%P0Cd4Jfx~{v<W>P!+Is>kfS<X!G7bR3;v*FRGpw<Ie@X~a#o~_FWdN6NB;u}l8%M',
 'test_reply_email.py': 'c-qZcTW=f36@KThn5=<t*_bQYZGeIeohYtzL7fX6rzxNi#F9ItwqEXTc9)SD*Fa_H22^MQ6ex<Kg$qAaGHr{cDA{of_#wYyS9<dwXnsP^nagsPTuO43hZ0Ck&d$u9Ip=)exs2?N?*$Qw><%s1{QGZ1&n>h9uR}uWP}lBuh<LJ08&+U{NrUWTBON!IOYndio*&ts8_IPb@t?C-d7X~u8jYS@@OE$J+_3B86r*d)$)C~2FWIxtOglPlom@m$eA<ktRd0H(WpioGkX*Z3C|n@NLxaS7$yU6RY{Y|PgT(jaK|G8{Bp$)oI*uosB;JYlNwOO69B(IU<mdq#UOnDE8W26+jdw_L7pCkcYscGhpTzz6Fn$bQACqJg_C83~ad(1`lZ~SXC3tc5T%SS|^eP1cpJh8*BA!oOU4!$r?6!eM)h-e(fd5gq=~=ehu4>(=RsOkF!jrf7O8oF8q{=+Oa6Hq}Tcz~r&4nB9Ub|WU^u~3V!KW^2-N4amMi>RQua^qx+zWW>C&@aVkieNA!G8nP+bCI!4+tuiFeUesO;ls5=yV6WMO-gZUTRR+3h{h;ajsYz3q2v)YgGczCnVXAhakz_to~i_BreDyj1J>Ih;j4)%!>wv-@EV#j66ic<1!o{f>(h3!N&1HJUElE@S4-)WmCo?H_VXML9w9b@x%gMX;MET@7NCg(2L&jx~_FC2)uyr><6|R>Dr6GZ;u^Q@c@!M2L~LWYi^+AuYmW(PjP1Q2UO4~?!Wl`Hrj&Vfw_mrPleiW2+sUe(G2KH|MdM5PJF~xfaW&v6^6z=hOXEVdc?VX`vR(a57d9WUty9Yn;<GjD2fS^05FGW!Xvb1vZY#_p?SdNMi3t)8|N2^lU-esT~+cNoHzT(FfFT&j1vIOx{>LK2fAj_$ZReFCT|8^%GC7zz3qEwyJv8;HR)@>Kp-&(&q2J4?m792kVf^U>6;DPv7?@@wLPz0alCdLfc|knTOqvUwgw`!yr5&cO{!Ihws8Hrc89$di4D}-&nl6z7=Uvl{ua~-yoWrti;~4V1x~DR>@mq+WishPrfOEil2~DM%oV$1e?{xdwrhFIpsr<LZrCWp<T{^ykzASw2@4i&k)Z3=!-)F2*~A?$5{rgSpd9=mpp{Y}e)u$f%v~HFEsc=H7k~Rxjoel?xWiA2AWv44yPUJpy&fU*QSXXVGYnp1|G-k@Pda`rMLgC!AyOz%qE1Uj=z~@C;^%I$v^ZbOmFKVj`0ux0Pl>b#=-VO8#Rm|So`L536>>X$#T^ZmbAfZw{@7n23O!K5)*hVWA@VEO7Ll^agBaTwc@Wv`5#YWrscsXGEPMjz!7Lu&GN|G}`Z2*h0&tH&*d6u?ly&lCAjB4rnS>GCIwLuRJFa++u6ewDevt%|e(t{b^Aj)(+8=T8OweTICFDY`95Fa2&oTDJds<1R83;9w>s^*n;CkE{wjBxh;fg+TG!HtAlBHqcyr3fhV+sw&>@+O1LIl>@G}6;R@){|2Oxv03&@eRH^vy52H0V_?zv{z}>ZMnso=>Z`+wfM3B}f%c5)BT3DWefO6yEuI2?H$ikcTMrkj3(3O%hf{J)0P4SL4S(VL}PV7*p{Xx-56l_&)xE6&pxMJ4b)P#Tc~ETQ?aQG#$HntB&WX+f76{2VgpY!~`^Ablu2y^lMiQKcFF`KEOw<I^>7Q#C6AOnvezRdJ4(6d&X}*Uby)lC}3{RTzt#6s!VAMK0p{I11#U}Mv><hYvgwXr@*@+(+1jqYYBMvBIF$y$Z<`vRMXhTr4lC&VHCPTo85@kInZ^@4BA~3Cj@RV*tzu5FMzMpv+&i5#(xS9l$v}(6CnA^sZ&r0TH<iZ5{w<#9)~O$-a_0D5Noh_6*+RiL+TF8ED#h!#XiiP>MhT)Xdq3*$Ak%f3^Rqk=_+PuI%XJx9io8JvK`S*z3!SFT7*2;wMaTIqAQS^z`PkJ1M4vhXLmots&m;qqns(bU!JzRs^J{dpJqR4{C#7b9HyKG>^0>|GiVOR@5aw?0?WRz<^kGLJfUR=VN|E+rqU5I4t)ZJu*kEHuMyh{798<Zg{RCHa^#nEB~yB3y%asocQM57VOfInwnSM1K?zb`_0TLn?z754E&+H!6hs-6GoIJ4(-BPvlJWhrAnmeahtc#1^YhZ;C3IOWv$kVK<;ZL}lz$Dp<=knO{pI3Yf#=X_u^re}v6dNvRmEEFI<a-s@T?yE6U^Lv8lR{pCOlwf)|~WgFbB6DV@ntv!z0?8F&Y^CF3(JMnH9m-qFNCp!PuLzVA<tqhKRG6=Ybo`4KbMj2R<u=VbF7&_ua_*wN01x+YPYotqLhNVFC?`cNn-8|CoaIyz%-EB8<$QQ|zET&5H~9U=}DDQv<{Wh#LbK9<sa`^O)p0)?fFN=R{|~W9bPFjYK)77=xAh?7;{t&YhzH%hoU?AyV=20S2ZL<BKJrX-Ad~P%QbL-}Q4i<8m%%z|l6umYl;>S-IC(wh5IHR%}AoEht1JC_^1Ecyr<1`iBc2TmzjUX!wG%a8DYDIzZI>V!O&jTCd^P@)h!8?HMMJS)G9@4p9?WcMl~$v#f})0vfwanDFn241E&~FhT<uhAczy6VRv|xP`)5U(1tLUi)(`J?5F|CMatarX2|@r{+t(fs_{vhG7s)y&gYApk=IA;xb7@9`c?EI1}#28Uk2N^s%~P**WHbeU3fw#gyGA6#*dLh!0rWIgpghofOLsR7fAgS+a`WvnBd4`8DM0r85#S*#7GEg-<?_)^A$3${uXtn7wktY~Hd0&o75d9+a+aO@?^ICodt2rz=sc>;E`FjsaX@8!Us5RK1Ld5Tv};uAsjD4M&5?duSGdo`HH<1NG<_&C!DU+|N_h4qylHn6Z;IBDdajJg5TLTdHSJl2lCO)f=?VxCDt_iB$Q~iZMQqG?Sp2nMv_OLVD%}dD$5|`OK$G7irR!2@YKGD&?c{WyffU5nOoOo=7uL@lamm>rIkwPW7$=Zv4LKc7jaFcug(rl-FfY`<5I|<D6(6z_FFGTMnRL#y<RboUEtYoNjR2{n8F?-aY!k$Vd?}n~w73l_z2_m-v^&z*+J>JJdj!QRP4tenNGpbZ7$84(a%*u4P$r+^HV04sSnZp>mxy!&E9%%~+aju5z%-JAkoYU=@wKzoKR0b#BxHJu|}(Sq_`Z#haU$$c}eaPaq@r=&VV-bj9x;$`-|U|50-Hfcj3a-e7gF48&qAnl7|Y=Z>5#cW#bvKjsGmsX<6{N-Z`y4e19<;hd>VY)m+@2O36RP^s`2XREgKbSdhmQY%#{dAXI;sT7XrH*iHM+dIL4k(<VhBQ;B67)1<OdVseO-1Q!@gmsr2`@mqJ!n{>dO#13rbaMyT>SKn*W{*4qr0#j?l}t$ORsiMmN$JwK6z6j#gF%AiP*)cll*kn_KL(+^m|M1^<`OuI!Dh+Hi{(o-C4zy7FIQ1zq{8JHZaPbjZMzV(-n;n$-g6b-@UQR=7)jB_6`Q$O$X=I>Ae>;rvW3LXS?i5C|4I?Fc9f_zTNPj-v+G27I~jpIBIr;jR7mU`I?06Vm-~P=f5N+Bk?r<6O)C0eGfKQBEsHahQC<m9R$7V&)UsI-2|ET|*zW()Pzv}bfP)NuCe$evmZaxHV>T0yyT%F+gK4b^8s<aMkJ9cG4D8|!kz;>F%RskHs+X$8u{6TmVyYo1`IIH+Yl+Dt=5Vm0kdr8QEQ?hA6HxsIFFr)8s2}f=4{5aQ1-BFy&U89u(eqChdN0q<Gt<CP>{hSt^0jpsmbOVVpv4zok80U^>p5$f9uVG3;t3I6ysYvAh+95L@*iXL#@K-A|M2)<1itY?Xj84bI_3&^Wfa(qs4va)(H11lW)#s5Bty0fd5_zsx-wO{kj_@bZHnH~)-yMTN?wW^gQ<cZZkw%sr-~ot4Ry<mO!Y4dLY?ihsEKBlRx2sr3sZYwL=oHIylBa@v>K^ai6(4kfZO|?8`2xJN#Q7#R>@^MISqsvZ|Iv4dqS<YsL97#Eq67)mY0**Eerb_2yj9rF;zcdWJcX^Y7rk+H9PSdu);FCWrgns`>xNJ464!QOrKvp%po!~G)}rlWhU!49csGbPYv)j;<ob5>}BQTN4dQG{@(UCwMl&NmIBciK7L=xjd|<g(;L?-<aYYrJHRQQFipTHSIM1OIuS>e`m7=jD<=jt1%`O(%jp`$!Q}iYHmxgZFBx;}Cpg3bPCoh-BLln*XPp>qMd<2{o~Z9i#tgepG-_r&rq0Bfes=PiFm~E*m!7bpnk(c=G*JY#G~}H0k17~x@&*IDeSQVGa-ix*>MUckj0`7NVX1u}S16oR%}teSK$_zIns@2H<x#!QM%QI~E9;KD;|83b#R!qTLe94-+4CCC$ku4nRG%%-n1;}8_@+uo!F|#z<?ru(y($Yh_0~GCWw0wM2qxGD;V<HX39A00i+^JCKgk9lg8',
 'test_reply_with_attachment.py': 'c-qxkTW{RP6@J&R7&AbY+i2-a8=%-^oye+^7;zlKR+<9Jg5Z*~E5=-sA!jXZTmzM1U4RNmfC5EPv~b~vN>*%dWhocuLBE5P-uwsZpU`t=cqexy+j>a#U~|bcGiPSL^PS6#*>@d}5oY%3lqsIS^c_2XcKoTX=k$qBEoz&CK8fBh(T?Gnx2Tu@tR(LheGxuT#c`SG*nZsZQ}J_rE2rOgY^5`d8(bP5Cwr3)lkPu;=dtqsz(pZtV8-H~)6Vbsx6d_`9oH^yM3-HvGis>1V;iQJo#vCd*>N4j4QF%|o?X;TSb(WF$kDDsf+yiduobQaqi~G`4}wv!8|;x_58kcf`*58ETftKjt^`|0o8dij_>jL|IodoN5jofnwn%svM7G0wN1MS833h_-gU9grn1t)l_kOsFy%YQ#t{pzC!@#ZA`kP|jusKEGZ^>kf#Br%DORyGQv!@_*q-i2~@DH_h$1v?)OB%3l<F`^BSE(yn;-6?jS{!eR<!FZ7ttVgSXRd!ZH?Mwn{R&73(FJMXSyEf^nP<9kNp$X$naioL(xXh4nC8L%D(!2gg?dT#q;=AKcDAyqu2(jTTU{E{tTU!v($MS@+hLjcDbzN6TuQliwpLHqr?3idwFrDaQ8)I$Jgz4$k}B2Fe5%6g!emmxDY~pvmyr)li(Ylu2hPAY<~+~wM9;2g+A!hg|J+Q`nSlWb4*-QD#OGSDAB@fb1cM(@GW;{5bT8O>{-@1w9RvXLTLR|6kHIc<beF#ZaR12h4nMZ>J&`}VTt~r2yv5<ea1Do0B(W`Y*<`rVuMO}w2#oh6*e6F%n_QD{9aI%&ifV!;V4b^QUAu>1uq52T2|bNfN0S~2z0s2Q!?o8}NwBFJvuP_PQkZZ4lcE`hiWKDmquWfgq7SlUP^RgN0LyuAKugVhFcV#KwT@|-Y$!`T$LTdKr`H1uzUI-c4-Ici&~4Z8`kJj%sY#@nD_5jDu;LNVwNkgB%<}H#sQXraw0hJ+>1)eo-~5`YOQvl&OE8-yU}ESf$IP;jo+jtd!C+Gc?GkTbt3IQytZ`DECI<C&ur&M;AwQuh{PU<ku&`qxpD|=Gr0C<B7LjgzeEFJs<<k!(qS*$wuuR8b%$mo9kx7k<Qo+Q8L3AZT7M}m(FKu!=)ASAzRJ|H*ge&1)LDdMTN67R94J3szx4Jq0A2dbUr0GZ$El}<I$echfG6jxtVbA2+7j~__aIQU7rO)60_1~YqDXH`X><ugrK|KOr^b9O?r%7%nL)-xm!z~q!ZiJeGKMGfmHo+WV3TUAtMN#S!Zp#~J1V10)hh4Ny^hYBwm80DzpFEg17{xC4bl|-nq7ChFVX&CB;5!gSGe;&N!K3hAxN$hb&-jyb!wx=kgTv)Qf4PTmK<#e{e;8p~u*rv@Fid3&+k^3)CL!#>T=qcQEpF@^Lg(DnV3jt6vn8AqS2-~vMPQ2q)C>6o$#EYzWF^=M*H6(WN38sX{rs;#z?Ks}$VTuiqTJ?7=!?9Ife8FMfFFColY-hr#^2C8BIGS1wu{Fy>k+kcWN`b7?bXuy9Ybr9hyc)MCeG(AQbW&qwoiRu>(TeV8c=W8y6~n8KU(MCWJ8y>OuOSO*XrP0k$#bBVMaVk!YSb7U}k%fDPdHr_!fn6-$sbyJ7f>tGWDA(j-{G9vO#KI$xCE2;2vdQGt-jiW)&A`0%95<v91a+9<r-yIl2a+pe*Nz;L=d}!?l_Dk3h+@XSId*O{2vpHsgY!LIW_qO9RFnyVfRuBq##oF$@dk_ZNX{r@_;sgT^+sdRt05uh&!FiWZPAQ+>dwD$H7zAmACGYCbT5!sjX1-vRDU=9Tu4S)E_UtCQ?gVToWW!lc1&aoG|05AYX&XALcR>+o-gBXsthCZzIu^Q}|6j%83UyX4}1w4|r8?76qF1-`4<nI+aO&G%uAnMY~EWVElUw$`V$I_LaEj?rZZCqORvo@06gefx+L%@*Pxc82d>zV{QfI+gv*En4NCUKq2d*=?xUR?HW~{#H+*Vq?3e=SM+yc3<=Oir;30Pk*mvFecY+L<G{XOrMqC@I9|DoX72xO6~g^YcQ>2QSs<GOJhY1^VY)qo@3Egt>>9Wt(|)XEo<$uZKEMr$1#TRpEq%kGInwK_+$W2<7AS#f(&+_$K6W-4_-Q!b=hXl?@hWS-|oP!+-#DX4g%Dx-QkeT>}(|<&na)eGTd{0SHe0YQAJkOUJhfFy#l5efd#BMRE7B2b=-kF2G<ud6EZajmoYStrq+d!Hb${817PQ8K2)#Hd@={>A+kh+Mzn9#lj_CfF6y!>%9QZ2agjW~_YA!}I_U5KlavSH0ebH5G0wn5Yd5y#mEbW3Z)@C+S9!dbjp;-v2EklL4G}oAfoEp|<Eg2a(L@9rBL53`==NAd6zf1OD<GD}cq0sp!@C&F?HrB>(yCA=8L&Djc)NZ=0)Z`<y)tv-M!X5SakJq-7nU|`bTs{@;W=)@UvwZB=}B2?&TRO3#Bll{n_}=hn%SyuIS|jF`eXB$tje*P%uzd3<yb~)DDd5Q&Wn6p6{5!aCIH9J;RZN7$E)&pPjE}de%*%9d_CvJimt4@60s?d$(OPKN-ejXFvT7Uf={qx$gw$i$K+8bM~!LUGJR8IzORfNskj2w=E1{%RC-6`5F!tHjPdq9mgzQ9Tjiy`)!2|91W(am36I2gij&MjH2rc+D#`6zGkuy$$Wq>bA;5klf^19@_d#pUrK^}W##RbxKz>K+#o7-+(n;!+=@w(aj=i6eN~B)N!m#u_MchTUN_7+U7feFZp0l&42w6PpT0^zNqwp-ZNAFoV{6CqUj*UUZP^m2{XogW*bxb5#6hl+Tn7l%itB)Z8R%m?Yc+I95xH{%cW}Db&rEASDR+Vp!4KYa*<?Gm@Ue3Y<ee$=jo$`uKUfkcjA7|%0Kz)jk05Dc$qr9+yH3`6sJnu}C+1Y6<<kk^ENewg2X-`j21RkcZB0lj|EFr0Qexb>x?G9K>InyK(z_PL3%O*)8B*=YkM&3EKcm5TiyFlZ@GwA}0Q%D!`P2-x;G|)VBortH^Bi@cj=}Fr>bL13P!0j3;9>vIo0B}+eIH?;v%2DR7&d*(+(AR~mWsAxu^E9wgxx94QV}fQyT$37wPSHoGT(g(UQF56-Z!fZc{&*Qf@wW6DNnc*IOn_1it-SbjZUsuFo?SiU*>Scc3rnh}ro`(naVSmZ9jUk}x?Zsz@%hQ5t<d$CqT(D*@_SLF-y})un$$8H%<1(k+7MDvAwY=;S&(b1Hmld#`P~!hm13K5XxA)D?1VoNR45jw4X=(Y&@IMqI_^T_eEU_g7k79p>SDp^WQ!}Yrt3wNp*z9a1BMwy23jrwsZ)uhODBO+=NE;gOL_@RonJDVI;Re&&WZ8VNda|fBBDCSKq@@I^K{G>U_*=W8n}1@t!fMp$xz`e(7GmsqOQgkVfv1*;FI#DW7;zO=uxIG85n&@#-QIHM$uB*k;0Z)CR$Gq&68fC>Cy=f%(*7Yl4mk1OQPN#9i+sei->}GxdYhvk;oVDtYkfNw6X=U`UXbu7)0~(ZSG`3q+MxUKg~Dt%aLGjT)CqJFkZi}VPiyBy6xhOK89DO^Owe#&xRIN3=@JIZ3unUc%7>D4ylkzQ$7^rzd$j7W+}VQ|7F#!o<t^yNw)aqTt3b~WBTIUEd-)Xmxy?(>5vxnXl<I@CY?bC6!x2hc>_xB)VWoSQEpOExCDH(p$7;Dkz19+;;4|50gZHOL47`2juH>Y7>=vIWf{@zdRm{J5RzP0%HPYdz$l|m>f|Chmp8rmHV_!Fz6kz8;gWF!#A=}e0&2fT^oY$%HHB*Ml<Pq`G?}(dy^rQU!K*5@cioFQ>WEXe{H+BZ(XHbp2fX}Hpo8o+jXi+L8mE!fm?_>p>t3vJiia80CoduFv^KC9UZrB3bJJAD@(Y!U*I3VEO!~M#*o|Ka|Hw>x*w<-vZa1bhuhT{}p9bn2r|tY`Ao@TJlOF&;k6^t8XZwG;(FI;97%;NR4p-<PF5smqaX#5bj~$=n^7?#5-G)<Zxojg|vr{{?jY2#d@48s#*R%nAtW%8K(o^vW1d(VQ;T_ZDbPoUG>5i$_WEN>sxhB;sx6q)7*&V7jWlN5CQ@wERTy~|Cs^-G;Z}!^xn*IR~JN5~LUuz=h*x|TZ5yS5X+c5GvkwJdM&*{H|#z(tH{~_?S#o@JHFVy_|+A^Ssc_t_J^XH~=1q$$5wC^%3QF!PX<&1dYc253q2E8P_k#jeiGQ%bn5Sw{J?7n;uQ+WW88BH}bre&`;`ZDirL5dC|rFK2@JXP5bdZnl<lx2&KA+^ED66vbg9|ZvJI<`-*i)7!Bnq%2676ql!PF)TBmoK#!r1-Pc9@~SsA{Yyb8;^J?lizh5+sbDe8~CM$;&pM=3&X)KE%B>m@T~A>c|rqNF6pf1imMZ6(GDcsyriGzL{FewRI{UNkT_gaBYQ7@t*YuTbJgm_{mpONM3nY{O8?EtR2+8^dFI;XOmSQsi+y$-64%?w*mr<cZt#_Xw_=IzOj@I8+VL8<2pDYhScjJ}W4x*+sF_!D!n;8F&yF^m{CX8$vcW?85BLfu0-cjjKjzs4-o)Yuh<LqN&fXS^&TQ(+1We@57bl8Qt1!Rc96vwwv!*?u$8=nbF)B4IoRD-S<gw&JD5p`rOyVBh89cWcW!EfT$J~CFbUFU0CfPfPGo~h-{!EQM+W}(cx5~wl*-r422m*Ha+tv7(HV<8Km<)a+Z&wlX$DAJD4v7wYl=6X2*{$SHbNH$uyhO)4!8VB~E=GTHwe7|IZ&u<Hp9#0>s!kBMqhkuLFJ`{{+*{}i>4Iii5urzZ;;RAPDgGZHGcl3',
 'test_reply_with_signature.py': 'c-qxlTW{RP6@J&R7&AbYTWje{8=%-kPGm(%j5xL-D|G>7L2$|06=N>Rkh7LHu7TRHE<gn&K!KttTDb5-Wh=I~vXqPapx;4CZ~g<#Pv|)_ypy|<EIp+AVDoZjcxKKy-?_|@*>fF_5oY%2gek7S^c_3CcKnHs=k$nAEoz(n9*LeW(YE24cc_<ttt8JCeGy(z#c`SG*nT|jy0{%Z%IWnSTWJsC0hb4d(cY$mWcp9xdL+Hycaccxn=$z<+WwHgyQP`zuyOGqy6jS&QA5=o+c3rIG@s1QjG7=GIISb`%%Wz(228v~4z?8%ya?BW&2TjshN~oa91Mf)V21=d@N5O2hifF*3|^A(ez1A45k4gQPx<5f2OIlCA_q@`O%gr;k|*KAgN<N|1Y5!P!E?BLPQo>qdpBIc*$KW5SNEUR;looW`b{uz(3~LfTQb=qaa?N466{6C>?)`_(j<{Q_=noMW0-b#O6s#t<F`^Bcc~*r;!g}AQ(WH^%h3$EQ%~N`PtSckJFk8|cNHiE>4MbvEUBgV%rjlNL^}J~^p%uY=~5<3O!MG>mG(5#LcXMWGCCPPGgCQK*DHs`qb`pa)*dk~8EAHh?Xb-H6lxnjZlzp1SF5M{Q`m*GQv}{0X&Sq49ySvvNttSEK2>3NVKFJ;1YOpt%g9HjMXx#RBd2d0v!3U8VrJJfZCLQ@e{7`MnNb50?tvB#Q9oCM-C%eIR517vDZ@XZmhJ>wum89at^on){H9Rz;KyJaCVIdhfpY)I^&M`W;Bz8>ex;6t&-jS_r{OAoLXm`6=(5Rhr%$ZlZxQ(3i(r==yliq#!Zl!3m?^ReoPc$1gLQ51gTaz;9T)U6W*tp>DELN8-VIkz&XPb=HAd5^7)W8g`B#c&7%D=P2Z(Mn&5B;gl0liKFM?Xmdwp6O=7X8&nya-<%VYyt>N-xhX*u04Snv&xc6=CkSAuCfj@Q#{ok~q2O<%n#-Gd#EaBeDf3(5?iUXG@p%73jMjZk{pve`4grs|Su8_p7}W(klOCdwhRET|{Rh4b*S34?Zs*SA%lQCHSDs7?}t`Z`z|-b9+8z!d&G>h~?2SkPw-84M|Ud1i`8H$S~{L%n+aV~J?C!7VH^F&MMvF=1p<<C0V`F<}rLiI9cYfB$of+|3NVM+8)_gzMq`@PUA8RH$c&^aKqgRby^-v;038im*x3FHy8WwdW&p0=UQ&FvbO$$+a)+T7BVsYodyuzy0&SKYdeT=>^yuSRN|%5PZ=qu+Xh0xto0A9(WjTsc3XV<P`i-xN@)o<^W4T3mqzoQkPIHZ=n(V=Kx=9qiv!;8iJ`DY&ZGh!MwpJwz;PR@AVXIXonMn#jFP30V$d}A_)neg%88^{UN@_TaFD|c+CwCw+sE{4n6_4za{))h-1Mfp8~_MluaBD#&?>4umfw^0d6<Bv9AlBb4!C=S{Kfia8O*~z=#lmBleIl#190=UBHn0!B)6-iat3)<uB~lfB6AKPWVUGgI5vcHjlwC;w}avaJL6HJHd+r+eF5Dm>o6bED_@3vCLWw?Pm#(WPS)Xxsq^Gj7`_ldTm2%k_ZdXeI|bBEUBRrJ=deYuXXABU-hXsn7a733pZ02-ev=rPMLPwS+3Q=&ms~d=)&T7z=W&8b;2TdBCEmxSMe<h-+c$Q6`vuH=$5J9R`FY^sUt9?mX<t3U;`LZ`ZhByd3Hu|0Wl!F0X*xd5bhz+s+OZ`5EaUD4ihd9l;7W&p8o`xJa<l8_`o!#_`;@Luvr)Yc6hnZm}A#k<PQW%;Cl=sMEQe7fZa)O`sk~1Os(FMlF94!6vCnnq{~$AGpY&;mnDdO`pB9OprG(|%Jp{v#*=lWGh}w>*YWNoaw=>QEJav1m@sZT+Q4JH13g+rqu$*AE2<RweU2DXdB3^n)Q)2r)XQ$Ucph!(X>5D$DTu&#H9ND#x~2I(>@o8wZJ3PqRMpmcv{vWvpU^S743P!U1>bY^UPm`S<e0OGrT~)R(#y|&gi)s=&)lX}%Jkw0nP$aMAy!NsgnX+PP$Afk>G@H-ot0}|zv8DE;?tM4494WTjR-&*mg%$d6E5@m!UYtcR2tvYSc7S8i;7FnSsF=dn0FRF@EnUy)w-T()LOYmFtXMfIX3zPYdgjO{`1Cuq^!HReS9&XPorp(wE_)JpVzx%DIPp@EbEHRoZp#rNxs_#soZXonhpfitKH)&nUQRzLY`ONd1H0Y&0VS18Hy^fs&;r7uIv<adJ#~-ilbHtrCrDEyCd}aVrD_629YyH>Cw_U5Z%UF?8~6A^V1)z*QP(41@=(0#DGR5H|k0CVxAXGSru?fc-go_UO#+=4j+AWxQF@5<8Tk1`1crcV9vE2+w%S3ImU6T+>Tdx=$8%eL{tWGU4{)2L$khTXJX`uiQ{l0;tr7t20V&;E`p0SfR_6}mWF#njF7_z7}ss>4++AmU?=%tb$;+p{fGbpBAB^4ee-541l_pZa9|2c8#LOQe%tUIx8W~3kd}0%EHq~XegSnjeUZ&JcuLJ|Rks|7XOR7oDNUB;m`&!WZK`rzMrbJD-Du2<d|Z`Ajr2{R9RCT|!QnYxmA`v|A{qJi2}J2@IX6~xW#yfSO?gD>lvSYAa?80>?4ckI1v`dxn=9{#l<MeOW7>C2-xNvk8*7eK+<|KI;F$n2y(Q8KkrF+}(0dmvcI&CF@~YoTY{-v;muRqr2jyGEMP^kreRD`w$?aP+eVS6pQr>_ez<wrzY|IyTf$I$s+;65<3K>COBK2Y!h#=@BCCgOA7_j5)XQUFSSE4X%J<k@m5v@|*L@5UIk#y$lDk?%2kGj@CZSyERi|x^KRu2D<W~U=#Q1PkM78NwZD8o7=k}Q&;sbfrDLCV?3kN}G{K6AWgQ+&8O=1f+b*k`3{&2CneZ;cHx$r$B198oW4VFEt+(-UXEVv?U9Z9Iw-bsnI;M3n$#tVm3GjRDIOpfmEkGf8G<Cb6blM-58KnQ3}^dVHedVfrfK6JNz@l8Q$enrzx`pT&?fNg@KQAluz+k|aWc-0NoKol|?~Z$WhzXk3FP9YApk=|X;JTt1ovn1`to^0bh|$MGmV8JkCr9ODYOT|>oF8MzPujtc_EO@pU8%IvlI*|{-uUCdgxD1tIi0~?jgTbDgCXja5EsZr<@eT2$6J6?{G%l!Fxk^S?_D;SEmq!T24dDb!kO0{a`$tQC=P%`!G?jg>OvL#tqQav>#UVn*0X)^CfMWN_=g*f7)lyRca^<zPCPEYc(D8g@&By~(`84c!iyB2K-s;Cg4M1U;7b*eU_*IIe$3HC~{%_wcxEK5kjAFEVI7N-qwu35latiS1Z7aA8@Z>oFogokQfOgNc{xKh`2y{KjAPO$cXVFr-_mP?A%uGFN<M^UBrFG`m#>m_As|B|(-ed_AeKC(WwQ-!)bR-@X7s8qOzN9&j^fIy4t)pzkQTGbeymm$MhMeCRlin<zGgylQFf>+9yj%mwq)1^#bGBEm*jDD{-h@z!*B84rpOthY!pC_}z(4`}sopVl<CC_A3mPEZfI#Y>57ZC;XatEOCGm$UgvB_HIlw}iQ^>vKkF^J~n+uR|ANW0P!f0}RPw<FQLQRR-3g7Nx&4F{ukrD7My^|5+oCO@`*`D|cO#V{eb(FQPAjn}Da?~)3tH047=eg}+!YL>F={4dLH^&&DsOd{grxqMuK#`MM6JE({@T_WPDrbAlPrL{?Nm$dtBVAyXG=JhGLSLaqWg1K=;;gaH`4LwG65V=)3ERG5}8Ksd<EvU~&%TeOt7=uyuw=5!>9Z&1gBdR2)mGUhb78qqTNu69G=kul)HwJ+L>x<wo6iyirKwT|VK!EKNM2|SUR8y!{o^m}Xr%k49Q}2`c&#-Hy_MUqw2OV+BmTzF-5#1X0J76C~0S>Yq8#|yTs~kpFVx)NQoO`LpAs$vxAHRhlX{~QD?5biMbJJAD@(Y!U6YS?9CVkisr12}^ADL+ndOD5H?M9U5b=rv5(?Fi%w4EOfL@%ge@&f>v5v;f1Z2wOMUBH!s0VAqxafbHd0$$1z$CD@MvE!3mUY|b|ScxWxO9WBU(nKbr(zEEw;OEsu7HdP)6K+!+n*$LRs<uTTY#VEIc(;Wch&=~S<L-pGHc~$wz7YvAR#1JjYikhOQWd1#&!S=arYgK0XCGri+{#K+E#4&zqH;AW8{2~{^K06GTb*Kro1@LT`!~;ib1N<BTg5hwt5xM0%vT5(9bUJN=NjRA4mk=y2BMnTn<X82sZ3O(Qq{>IYxE4gf#2t+e+?90RZWn~FG^;jGfNy~M&W;<ygzDjrG%webk1)}+ANmsjE&0jb@D}NoyC&S^xWL_Tk40`Z(XaTcD24wd8TxPxkP!XavIU|mhIsjf3#lE8Ig#r0_45GqIdrMF~S<r<C`3}r$=R(?uip2NTKG<7hf)Ui^uHL8eSres>Fo2xhQg=5vei`M$#dt(>M_?cSNl_vq|INBjqax9l(g$8K^d8OOAJ2y?Fk7cBhjQp@rAq?6mUdp?f@K0|)g|l-YRa8|Jd&^Si+l`0^U~r{{RC0`B`e7<{mO@NWWFo7^?8)eGmPJ#860F!M|v6kj+$kt^;(#7}!*sHROk%qrvzd7;TMf3S@i20W2-jiH&(Ce>pbKoO@eA7WP`X69?Ep)oDnCGN|7wgo9_<d9nR%=JX&JQ&eOQz0!|bPTBl_C%y>LOu#8xa-(HofCypLu!tU6k}3gDxK8TAolmA)`AqjmRcic5S`XBp=cb(-ge$HK5~@L08jkVK=HV^>xIvOl$LmhE?g`8S{^e1wo5vvxuWgt9NK||!b|39j*X&qi)wb%O^%<7&KKU#cc)hUG99ZwKic@VMZ~cv1X%y#fv9K|AoBE$E182u(NggF+|?$zn|%8opvq0YGw@Vw(Y<kd6fHa6<0%3L+dMQ`$e1y9{ED!aSHi;w5HP<w*l6-DRSXgFkn#t71Pg)5$@NcpB?cQ>dGiJSm4=*cx{S`d>&h6N$oFQ9C8JhheZM(;eHc@icAp+HaWOxu<gjqM+>sE+lD>KlqkNl0JMtMk^B!jREZ)bQJWISBe$1W74uYhKF(>B}BhSSFnE4;)kjSt9Boe4C{&Xd7amlN$Xv6`(k+-V|`D09vJL{sua;1D2UUn<_lW@Lks9s{?EeJRwh>Nv9=@9<;(Kq+w)ABLR$yMDKPog7U&M#ICdC!pGw`1CxWkrA<`H8Rk_@^2F1FN+I7y',
 'test_create_folder.py': 'c-rk+TW{RP6@K4eF=l}*iR@CckpP9-O)9H$8pMqSTR{pa3xd0xl^E}m3@@=1RX}Y>vXBbMLxDaNDN^*IlI6=*l4Dza@b4g{H~)e3C-j_|AvxUTuH;C$Jal2NxSW|YXU^q2=gf@V^ISh9q1~eun?HXVxK8@)n~vr7(qBR7+s<O8<GVc)&@OfCs7FNG9on*d`*Z3SoAvCy-d=(Rs=HojyH1dfyTN~s9_99WuA{eB(g9ajPV0M{u4Lptfaj6@gUG{9dSs{FKc=nUvbK*+J3MV%I*2ZNv>j5*XuFPO^VOLFnVqRrenA@N`T&8GeVxQllC5|r*^K+iCOLk9kICJW?c+X4wn)4O4KGf%lZ|*M-Xrj5AA0W}_v8KZ&ma0LQxyWAJ9fB4T#q`c0?X{!i#pngQX`5FU({*47T88ZiNa3(mx_i0=<t#F;X_D+8JFI5O-t=)S?m1t&G%;KjgM|#haSA^f)e>%rKzLId1~I(?hwZfr4c%HtN@u)s}of%pK*Zhn+*c(XCmW7_Gy$@m#jm}45$I@0`qyl3SDkfFC^FOF8$CAuep(9&HBFUbHW~YQm87g{=Q9;yYUWaZ=FbTCCST^?YJNB5YX+@xPOTx>+y5!nfw_P9v{Ygul}^1+=mYFK7Q@Q2PA$T?*pNG>{YxQKWC-_KX&mw_IboQA3sPok-DyMxzc4j1QA!bgBq!WHd5b&wqlcRT9$!U?*nW&q1hD;s$$X5Y%hU9%=-~79cKEA5e`z7dOZkDKdkr6WxHp8K`muyKtMyIZF*+Q?%Lsssw}$h;#AjNTm(~_^Jyo5nN}6xqvQHL(`i#>iYU|9uPbY?9PX^JjNEZ&7<pBYZxm<KDtEx?p??7cR6evuE>8l@ibXrbj~pWisi&H499Sb34ccI)_(RxD<~I28X%KahFz;WqX3==5L6ln`ygz4Lzww?z0CkytN`!SLEN-Go{T*e%K)F426hanWef^gvS(S#aWqM{7Im`aQd-PG7lc8vxMlV1&1-DbFrUxF#U9EoNRJDc4W~FShzy0I87hes`2Y3ax2v!LO9QUWlYDPL`g^9(q14?M+Vo>rxN542oJ>W2Y3Q!5?h)@Xs`y}2??&JF%#7V%<`xi0of4|xO1}HQ4183W301d$WfW+T|w?4)xpMVQLME~1G@56^j$$GMN+y@^NehI$2&;1?W0iiwQ6ki>2zQOx<Z~$Kuj5uPeSO>I+-VZNEh7d@$7;qdRL;&HF?emjGhXMbwJ1d6i+2A*37zHXm0^)iu7*b6HP$P)iZ5jj(#Eu$EN!%!GfZuT&<wK2d#iL-MO0tn`C3lm1ASA@X_@BuJJRT7B%H*V`plcP$650iGQ@Ck@*l|26jK$Tx_yr;*QQw-J1pR^SzKv8WgVz4lVH2%-pTv*3_+K)WJtY9ryCAgtl9u<;4q%RdAzG8_s=Vg4Dzh3QPY!+}EpbiP5udr^I+lUrfMw$!9lunKyqU^~2k0e;G==tGX9II52k=B>7kIb`_zG{-0)*xs3a@|!U>UI;HnNC01(1^_Ff21P<yar6jLL%213j3FRB39`^AHJ8T}lPJg-fobG{Fvu@*xfHxc+S&K+^-nrZ;Ju!a^)%m=6KGtQ+u>6ZA~q>;+15K}nlSSildD=xHaEmCBM5NO>d~$sex1p+Wq0s?3tr%9a5FyF-1@9*7)fOMjLxkfl~#YC0nQzySiY-z`FR$*d{24RU4jt<m&F`WD(wL@VRy72Rz-!F+mH<^p(Z4Vbvx96yMwG>m+Qr59uSqO+fY8Vf;LKm;d8uS6s!DZCJb6~vdP7(-a_VAzb{fj}%CSfsmz(dJovgpibZ^V$ewIUAR0h<ON%?U4+;;yo5^c6b0`k?ja#8Y>crjEra0!aEHD$alKHax6qNTt8y5KR!Y%JlVb^35Kx*K#ACwg*-&vO_bpP|12qm&JZ#8hzc$JOn8h40y1kuC20B>f&Q3ga?I_4<<fhF)h93E&r_7Z&@z*IAet?R96VbP8H%tOY1O;DfD_@VKe%R|$_;bwnL&`fWU(OVQpi*%^|v{JlBFE*gb2g`23HO%I0oWZF?<cyCoEL4SieXe>YE`o_|}2pm=KFR$kpxThB8lsFwI<rig**mvT9ZT6lkk_oZen?ZNL$g?>XpZ(6()(OT&=*0rVEHEql=pgBrQrcw5shD3d&dO!5%zl;x6JJVW~y4Sb3mZ-P#qpk^PVQDV8B>RQFz5*&0dmfaJ6APJrmK%T(uAG<t`|DD{`&d;%^BtLOp{q-5RBWe$=@JN)2<9HS&WTrce)rRe~+~qXj<avUcRk@(5o@sX{L;!#HvxxdDjVo_>@S}104NP7dj7U`*u7$9~(j$l_U3GRwx1G=Jz~<GR;dTt#rC1w6PSOSwvQ+iziavAemT_zL`s~d7jhhg9F}|6>QXQ%dN*zVh<k}{mCvybJ39jHev*ImZEKo&s0&mPxcvg{bGB1A+AF`bL2pyMW{z0DI^MTm;xSz?<1S{=%p%J<UaEZ>)al00TamYPzd9cRFSoX|tsYZAUbCXo&Kmj*eST{NHvtg~!!IHKhM)0A4Lh3e3gnyWup8s8q49%VjPtr79rtJtA=Ea<<q~&@5$%NkS+U?t__A5w%QeH$-lSwsW9E3Vp7a>;iAdvbD3s~!MU!a?$tIL8g3WH56Bq_^7$o3o(Q6?q=&vX_rzcFnmP(!*Ls#>j@`Z57@{8B>ns@7D_A+?<2LAl9m1ik=x*LfMa&m=aQp%T#{)@Q;4E`)i>qO%<@3WKp?GrQeXbioMOF)F$6eq&oT#D=iW8U|&B)dVzP#^+OzS^)Go9|PGfq$TiPw*$kn(c4#`V@U#xeS~aBv{BO^(H3B3g!{y*?0=_p#l2*Ge){TgzZU52_JBrn!Gn`40LBO@FVh4l)gPpZ5(jJJ9U+KXJ>04rasf1AsjTbRz;dd)5_5O3)a%+`&^r8VgJCqPEId8JB(~a=at$V5Y60nMCZtLQT_UN1GG%6lRf?}q)oE!-$x166Jxbf7vZ3$cp*YX*1i2VWGfGMQ(&n-lRAg%~|5D;U?zI3G$|}gyE4CMrp@G;8RtC|78%7Cklu}oCro;=2e9s43`>gbV-_J1N#*_i3D{N})#s4|k#(X9-<SmiPWG2n`NGaNL8u#E^c!ERkl*T&Y1cM<@ytW~pz8=OGgr0jqXN(K1rd+O7n-jPb5`?ZlHD!`NlGh*PdG)}yXv_5LxTZR;K*^YT-4KF4V}|Xe+0Sw39Arp-??wUTKdU`_c7aH>Mpj!<tJS5!6u44E*ED9-k`%SE)xkiPA&o0wiVP|G#6&9!L)TG$m|Q|K42Gkp<`l9@&XQMfOO=gI*skk^7h-dxk__-k@TTNT9?zLKRW$;@THdkXb{Jc~w>3$k&zD-Bknr}>gk*^Kv&1eV_5U9~87WAXx3ZRN;M6~Lsxpvc%-r~J{^pJAP-!Wqa;6bir)NI6H8(vods^=de@6td)6juhpv3cK+#D_z^wFRySIpJsxiapQ-|~o=nPXXsmc_&BYT9kB%Hkc{jLWJ$3znOgcw_3hpF@n3lg-x&bEC)oKhphlk*=VXvjjVCtFrY8>%Hh;S5{)MG_l&u4Xq^5@je$6-SV}SM>pPH8r?V_r-&5qYxunqp{6ab4V0s$dOB)y{6fS+%)AKsNy``#U}5cLl}E;ns1F!kX7ybNb5eOP3XgQviHTA;NmtJ-2YcZDW7bXXp)Fj7rSlm8pbW`DV1m-UX|b~OWaAU3Uazw|Ik?TYgM0N;B-?$-clOiZpso&1w5AatAxvlNK`S2b;0ZGBG2(pa-0S>cK^!MD8Y8z8hlE%gTD4YGTi5KhEOV;lL|);8l+x394R`Z$g-*}CPgLpH0#Dqf8gZ8$rE}R0d(f4!0`J41jVUZkK@hlKzJZcv*Edq~!@9te^yI!c#t_l_XRnuve7wi56!1OgNBrW9bm%1x8RPLMed!rtc3z1a)92Pc+xF3F#cWZwg(9nCFIR94=SPG>p=C#cYH?-kBtuKLJ@Wfp)9gak%n}PC{GB$K8qeOEnVy@~bfICj#2}fz*+rUy6~mnA7KpfYxxsGSpkVp!4?N5R)GO#Rwd6x?$t9;h^7#v!i(ecOc8wP~D|s1eodv^`o4l_u?sC^U14CRzrLMzFPhBlx>cai1xOX(jORY>WuM2a*1SfJPxGS1?@mO^3qxsxs2566jzM`cZZ{i^wcm?8KaVxE8AVYg^{MJEcFr{iQP-or<R*S~VvE%^3Gg;?TF?S^sgIxSbYA@DN7oz0QH-n`gM#r3VA(r78?AIIcPXLw(Oa&xkm-+amF?Qy@A0M)-xP<*h#MuzhU{~DYO|>l!Ylkj>VAR-PN0w|(s85Fvd~@*1W9GmGjpz84ZZ40xDViG@-d)Cfh=_pc&GS82>pd_Xb|*lD1HAu<2OHu-uKrnsXBhtj6A844',
 'test_folder_and_move.py': 'c-qZc-EP~+6~6aVOu4{{Y%IzS8X!=scC%^HrU;TC$#x5P1%e_+@~kP6OO9f@u7Ns89HTY57X^Az?4m_)oEYA?{>f%@ljk7gyS%{m5qi!HDgKDE<*ZUvfGvqLXXgBV=bRa_zV8K`aMq_YOn&}6^xX7wV7j)~PrrpcU~X@w8+d&ZQir;1&?m{*GVRy_dq9KYus(dQTZ=G2b<gL_bHkMGw){Gt%Io(%SMRK*1Rt-Cof{5(oT3j{I{8!D`K1{9)MWfDx|E2n_|)RmHZ0GzndH_C$+fF9Gar!F4|>4@CkHx-o<=*-!JGZ)-}rvAP2N0<cH+%=<7E5IK8d$Tv>R_m-<@p7k72?tfwzNrOHdsAa2{rOu-cp<@LFbkk$66JRRv`2vYw8{S7wP4z(49*o(%?XDFfcEUsg2KLRV7aOOlY5@EG0kOk3@0V)Xu%yT7`2-}vP2O&FEa7L-BYC~X~m$XDew)+MgTbF+2o+95Kf)*3Y}+bOr+g%*LaGs)cnJ8cCqECxGfNDW{O7|rI)&=rgNoLpxPz2))i-oUl51%VgH1$_tut}1W8-X`%zv;$^(L~{Bg@#~ZAXg}H^V8r8S|3``xm##1llF!IMFw#J1r7-|w#Ub6aZ3DeAfbev==_CWHVpDEfi(sSs!GKnhnL%%WM5<D+hujQ!y>G6tKKnhjl@WrFa>Fuxv%?(5S5>9wdA+9N^?G3aI|1#6u+y3Xe005_Z@Ly$nnbyB^QN*6;>aKZF|vTVDwbE1<y*zww3%fHMwnj+PF0f5lKD%p=8R3dBpA3x$f>WI781@9n}!y64}M8ZJM?6H$!UpiWp?T+WZ~^se{GYs9R0e8K?tmPE8d77g1vSLhG4V@{~r@Hn?5v~@P%vQ4M;HxXtpawzcBc!PeCMnQ>msKhHHYvMrjtBjX7v?2m_oKP~R~vs@6VpYqO+AYT80`{?c5#N`$}v^ZW0<9FgLA^b+JiZ;SScx|VUXt~JS8VcT^jQ%zv9kP@0`x<_3an4B7><1d;nI8MMUL&CiZaM|OFt;>nZ1Ih=1OKLU!bC0>I%n$(X9<ykuN*dh^EyfIoa!!MgTu3s9ZnGZa;VfBd$wf6Z^)xW`5HNK&Iz%juACl-OI*vEdo?G!Fc=BWlm^mFjj|87P;CrtCB@jBIWAOo4e*X54z$!jN_j~&0S^R{kw<ursf+ce0&JA*tK{SA&v?+*#R)=t7-BrVtTNtL#Q~-(|U;*H$560!QBze%Me9^O8%AMQy?qg<1GbA7jAB3%ob91wzhVTZwH9x22VN&?+mq+bP-l24$h65olNY^9_YlY3$+oZNu;%B|4>uFdDP&05-j5~PK@m~`C%Zq^A`KP3wC-_;)Y!=1^B*7QJ9|mfIXvhUTQ41ib6$s!lq)b?cFjr6)*GtwkY?GV$oEfTuXhG@IFf@BqX=}O9BTGQiOIJarR7GkFl5?v?l*C;CS3)14mfocn1^#VilouJxp%1*I3oa<W8JPW0X)h@03KcBiOJ+=*B)P!k4rN10CFx7LNr6B<0-CvM5|FcGd{irL3xG3RuvK=&YB`JE_@96LWuN2%tBvq^5Iu(q3*&IN%I{>lkmFdA!Q3OVCih$yF@3U)NxzUes#PxF6Z3YK97-9cD1>i@Vdkdj(xF2kE6(XZ(PpZ0L{YXBT?B+wN(RD{=nzXy08Pk<4?!6R;xS0H0~OA0QpluoB{Ez$osdom7>{*S?p}fi(GhGYD&u$yzwSgY5Xgy&h#{>2e<Xe+iZ28b_?La#$Ak`f;5YYf-_oX8FDHfHXYSj-eT#|)rC?qDY8>yR$gj-O@sk|TONV-nw9y_sM>WS!B+7{``zCXZuIJb^5H$q^(W%+`a)OS7&N->%b{`PvF|YzUIcO4WIpA+!>KAOV3CwL_g3bAcAj5QmrJ8|=W-zzot*E)`I|EU5SZ`k-3drU(5~%yd7Xuoswl03?!<W|lhgib2#6r1X%6b1q{Zh*Fuud#-0C+Sa!AA5Ae7KRUTbB8-Nrb7MqszYr!egXLy$?PdVti~$r$i0lcsen$YEd6nKvCy8E9UhAJ3qsv-#jD8C$72=Paeand@-Pu*d7nZ?nG4AvuUzyn5*qPj~gBCVo45_wLWk;bJS~BbsyjtnmVY&y9RW@*dBnoEMU-9)dJ>xysH21&XxPWo-I688jT+>e8lWlEx&QC-Dq?MoO|v9G(k{lLMNj`G28b7YJk~!O>2`ska4s&d$4e^ovtw7R)$+@npXB8x<ai1=u=j}s*-j&;lf;7w;X0IsoGB=siZ2Xbe;Jmw4?<@)sG<vRT(<MAq4Iwnmu&{d;-=<bf0y<(z4LhybnF2R)*UA$Z{YDfJ!ZUsqTRu9CNjvjM4zqTWx@x1o58$hf)!08i7)!Ff|dzrOSzBV9}`<BGb|&roc43hsg$`aYW<H^#@!ibVTD1Sjc4adJdhVo=xAcL%Uq3Hsf_EdcE)2rqgJM?W&cKaRRbZGf*pszz1w&iLQof8N{{fe155*jSL!6Oi)Aty@yF8;|q|!&#L1+)dTm84mE^T%#K6fQ6H5qHe_g84wH#f?J(nDe-vnENmn@y&7aBx8g#YVTG>MDwIuCSG)W5lYa{@soTEh=%{NC)c@%hv2Y?5VTt)r0g>^#wC_yGD$HbSkSIQ*8Li8|)R3b6R0-~6N@PyCk18^9^l=%#liVT=Mbr|c4d@+h*95P$of)35DGfw*@I4Vw)69C}MqT^K<Y?x&@UE!)W!Tfdu+qjT>L9;oQ(JB_14WlBD!73v;EAv~-;fBcJt-Pl7E(2spRI29UPd_`8D(8zVc<4FK4VQbrWpr6x>wp25ngIAP0Z@Kj#9YSbcwl<Ra6V({dHrHF=H(KxQi=n31m*FNNci>ta~3XhUy*)=QjIQis0h<(VQH$GQ;;+rI9ECy$r!kiOcRO-fC_vrVUPglcZR+(cwL6q<L0<3PLvwZ%4`<88tB?^K5U7tTkbSC$4zB<4@oQG#e~2{DT`G;-uaX({dfZ!)?=cYLEtSL4()P{M0@cgF{o6sr4aQV7=knif|7BmeA2DJr~1#w?IhI=gPUUMC)J{72W+CaK)Xv0-%~?Tbe~4UVX{k*5{~OFGNp~n9yT-aSPPe_i`jJ$Ak7gKn-*iXN;4I4i`Ez$`0vi+bPB10=_W#7JVvjoI`^V|Jlj&_QBfAAXSrXxLM>gPR`f1xH>TuPRjyQt#wjOL(sClgWa>T2tM`Ry>%SQ`{zuVEP_9yHen?LFLm1qMw_qJSfdrh2H=<W)46OYS>;UIv6H;xRLc5!6S{t`%g}uO^-j}_~Q8<>XDcTOinWz~P2bAKJH-4RV4Py=lhR3l&-@_BAN+PJl)=Ecp>m{Y*u(0QJo8G+QPw8|gQEAt+2H~)Klgw7|Khi2^BUz_hQpRMqc~K2pN$OW7hpB|3WP!f9M5ozbpNUZ^8`CNS6aFVC1MxTv;AB_+Kt&v7@5%eQGta}O+bHL(`>kFAtx_d7+WjUcwP0RxoijFJbt^HkxO_!?7MCyjiYy3ik<+Jwlidk`a+JlXp594mCOE%4d07>R*u=@}v0^KCj=0QGm0}Y*Y15H?#s4xw^9)T%*F{OH?>tUD`WkIQ3MXKb__eqRJhdSzwBgae;?2p9$r{K`1q6I@Is#<(ZC^buUaW~9%ss{{zxdBYoI)Prk3GQCwzK;`c>%XC`@H0bGUBFC{t^MNJ5fNaDa3u-DZlhd0Rve1dV6@?m)r`=r3K8u04fGx2!DNpzqk>0b&?CjqA_z`^2Gpu8}?rXIIA%',
 'test_folder_lifecycle_in_sent.py': 'c-rk+TW{RP6@K4eF=l}*iR@CckpP9-O)9H$8pMqSTR{rQ3xd0xl^E}m3@^46RX}a%hEzZv3iP2!k)jWkqS)C=vg4=^{vD+B=0A}Bgq|}qB!|1)l^iLThYGf|%b7VmbIy0ZbLL|AJl79NX!mHv=AS<bTqphPn~vr7(r-cN+s<O8<GVc)&@OfCs7FNG1KP5D`#$xH&3g7+Z!bXu)m<;NT_;G#-Qr(Ik8*oG*U?)m>457iXZ5{DS2FSM!RL|vgUG{9dSs{FKcubSvbGORJ3MP#I*2ZNv>j5*XuFPO^VyjJnVqRrenA=+`T+r_2RezrPPXISWHat3o8;t6{FppE-8t!#WShkM(D3c)PO=g2#`^^R96;}blYV?~@%M-R%2b8G&jUMLBCbarRe@=C>_r`MqST1u!!PQzT???$P@=F?|D~d#0Xlpn{_r8B!N8?=UDHxKTGl#0efyo+dE<lIH=zgbx}ZdUS83`9IZw^I+8yG!p)^9LjuoJCYIUNj<!>C2`+9>w`?<t8k$sjV)+OuEG6QOWx}bdCuR@pG)C<WCyG!49!y9hoShK$G`dqLFkrb-R%fIiC<YBxE-diV<T}krdbSLh|y99juH11y^$$I=8dnSJdhsQ_p{>wk@BwNrSKEPkQ@ga$y#|I$j5qlKx#m^a3;L9F9$3Bl)=aVm!O_Z)H+^%%l4#C6~9-u}Vpp7&(p{>}Yo0erD>V2RMCp5dFK~*don(ZY3#JnHT(qX2*7~vpQsn>(h^uv13T(*1mC)84g1_U%T+NNi=?5-WIsLG=2E>3mb#YKSHoKHIeylGVdJvy%6Go3b7rie0q^QN)})8WAi)5rsNhKW~&_(t(<TIB%*J@hY-fXau~$kj=ZS+Qt`_>p4-A@x+VjRR}MqCp#AieCh7varD)p9WDE1@rzzG>gV74Wit6@7+1$=B;-W0<6pMDGAn@u{cDP`di8XKslZ|3Ly(GKmSXUtV%=IGCwm!&ayx79AlK`Vkn~1=mi+25Oyln^uPnVtJS+sRa=;BR?1%Xw|{*1?Pmk;1HJ+*0xAK(aes=eW};J7m|09apoCT~hb0enjEloG0*>ORK$XCbNQLmfPvX5~3!m>IPXd2#UB+ww`^C-|Aen_91ls{4Xdvb<N&F0=^$EW6YY5@5F#h&1`tZZ!WIfqF=|c>PxP;g};PH;nK+ryFijR)D-Vpt}IDpRyMjW$QtOMIa@2@V$hLA|M8F3sVMS$Sbor{abfPwh2J1d6i*$_8o7zHYR1jhAT08&jPP$P)iZ5jj(<c=CEN!%!GK-_VR@}Wk!;!!}Tl58Z~$;0Fk7zw#B{%5iQ9}kIoZE{jmFtmzd3GD*h6b?-=JB~+(vAnt;e~U~>)Hfz4!GD0=H&IGu5bd8GH4)VZB!0rp|AM*fDFKq+1EXz8UOqq^z&rkhY)z`G@|@SI3^hc4ImC%H#Wh_=e&&JeSO%H{rj37e{H1E-_0&c@K`%k3DYXAO8<+<<kS8*`;KN1WS9qcpC^U~ycmyJV%ZTl;kwwlakeu`a!!kot&h>%Hq%0^s@PoNXm8K?r9ufhrOQm49aLKilCg6}L@6+&s>)+FXG(BK!dYiT>OvF-#^$^6%x`8gaK+p8eUZ6A=l(e}-1^nR|J?(_HQdv;~C68ny`G>o2Xb^v#I<sW9GBUtm52z2`1Czts(y!$cWTjP?nvN(xaDd?Kw~Lfr^43(_2Dvu*#%TGXd<$(SqLp#-is3e1VE%fT<^n`)4V1Xr96yM=G>m+Ql^0|CVz8e>8cRW0LWCg4s6-|vDZLP+737zvm_u0dVBC!4fkZ4muuOLav&}d0F;Y?%&1)mTay~876!R4*wofwhiuYNz+2sj@Wwv9;X>5@|WM(|47v5?RV7{{rmUAJp;rcPl{qZq!;pxs5$uLYMAWG!EEaf5VZlVnb^k+pWbcT$%PgH2>XU1bfkdRp$IziLN81%=4$qB~;tEKk~vrk^YpQmVnp=l<Mz%<*CIe4`oDinbkY1Vsu0VmQ^e{jyclpEIEGlL*|$Z|o@rBJC(>ThxZB~v-%1retI4elJa;26kX#q>3}K4Gbf<@!bHP~Qxx!M6?!$AnzuL9K2tH<WoAglXj}T*R9omsP9!M<83}<Mj5DYXgs{e9u8QgSKrOT^fee51_YrY}t!;7}UtU#+#aUNtNUgRFX%CQ&vlE^9t=50(^>`Y=Td|M$bM$P~vhs^|gw%B?RbxEQcq2K@q$rfI5NWAG<t>|D8P4F0QdyN#1o{{`DIONAw<|@K`Jp$LX9cArDbQQ0p-(ijJ}GGq&5XjkWYH3u6fJ%*mM44clqC%V}oH3ko$`4uem7rrn(onf~pMBkHd-uD#~Lm&VoCu*zvLAysX7(S&O;J%Y5;RcB{(+qrKCHeUuBZpWZqii=1nUfO^)OI5G0=recj7<XoG&d$u=x(zuR6QLO_)nQpesiSC`ya>wQlSPaaE!S|K*(xueEJ#HfgRsqN{k+T<7-9AKF$Ou$4~KadJ{F7klYVAO6A<0=LL+nyP!t2F<901b`B10e3}Kp)vFw@QQjPEy7E-C%K>}{dux@gdz=pL#2baGEOG3N_6w16&R{X=<^!)E?Wa#aw{Um48W!jEFVZQKFm2_zzK;facyLS7Ys{IPerBoMD0A+^F6bHKwuAz`udBRBJizT;pu)SJ}O-(SQ<i@Mwg=i$Ej<B$7Ct>poSW20g2t3nSz#7T4oj?uga;R#xYRU%?Udg9YR;X%C<pS2sH6FC5JV($A$a|eHMGu%IM=MlfI?NZD@jwd!JK1!$<3(XG)@)|Co0={dVLK)zH{Ne-tA?}@)>*@#t#CyG4Olh$6s#72Jg&z;g$$()JlE~OuxuoP73f$}L}MRe+YxQl^hdM>xVpl<W>t>MGrHn_v_3z5eYjr>{C01^qq*TB_!S^@+$emJ7E!7HpwyH!SQ{S*LDcHucHdA4Ac&=<VaEoQQ{R=q-NEHz*Zzdo;cFX!(WtT%_ZSP|YE!CLn0=`QqHmZ`ZWVlqq6*HGl^J#^K0ec@rOQ&bJj2nWygjO-`W_LA?-_nUZidpTRC2$xK`jOq)f%kfl(>)kHNcUw3-S_;?Pp|cAU2ehLH6LlDB+D#=~@1QGy$MXlNS6IaCPW|(nKYYI+(A-V;hp;s}XU*GC52;V{p2fYPnWzPT-bD5W4=<lu7<bUVV_~)dSn2Ez_^#oa#6OB~$8Ec^-jnhV7-<`?y68HYC4yqk!_S)gFF!K}fYmR$Ec4)uq7{;60*i8bh9BMQ!XdV4y^h#uWlzj(dG#q7{Xq>nJ}=As_*Rk=>aEf$Wm=B!7-n8FT`>t`}Yk=0;Tl5IFnsf09pm(q-IT)d;X(dB@Wotj4pB&F_yU$@KYD%c}<7URpH_>3*IBW2Eu_<5vs?%koy%asz_;r>-Xk3W1qh@6X@9brV)fim9Ay#P#W!_wLM1&&;0HJLBIGndU5ZpcXjsVr4O>iv@i&sme>^YV$&6ajI{5TFc;AR!2cf>$5$->T23;t;*JMY}YMIbrwuFU!RRxjQt#PoLmvUN}3xz?*EzYr^|E&ubd~@ajeSd6X?C{WLLHhU|U<&W)8HHM92GFQg+MdR-WB>duev#dYoZWyqMwlN{pJeyfRUaw(8le$@vQz3pw*L>?ciQ$bf~pmn{!6ZN#1?<I8LjmL6d2;$|dXU;&J8@r|)$1FtTT_!-;be?nAgH%FWxJm#kzNY|UV4vCM>I7ZJ-chkksa9Badr=T=MU9!c!4rZb9UKbuOk4A2$B%oK~$F80FZY=Icj5agQ;r0*VxgkY8s8qVMF5H!#%iMM9^*XyzgvQv#lZGjh?fc~C5^2U$R|j9TrV$V!;$iGDG5QwIztJoBKD7EeKNb;(;Y`NJ4bCC6*M?@T6|vYgdo9bHD!EUf@IgxHT>=gF7ju+O&%H}j>Cgr53rMKiV;2Fq?S^UL+E|0*rsT#Ho}{cJ$`IjTX?FP}6+i3?ya$kMi9;AslKkxbQiyGKA%e%~V}9*NI<gZ-r1AK3%JhUYJ8i|S@(X*PZ8&MQVhJo`p{VNEt0COO`2nYJXxV|LTAUd>htbjvm;5%`G`kKqv&0yJKhp;5{n<M+({r<$E<CK30FwEeT>~nh80mJ4o#mx>MmN}fAv7$%yMjlNK;;Errbs^GNG>_Ml24D=yZE&ifor^mTFKYe)_FKgxy}0uaF>VHITYe9Dh(Y5J$1E2sY{Qm;)d9uF10elyeiEF6I{r-=&lIy;-T)`2lF{*24s(<z9LdiHt`4%PY<U={vQF5!JQ3pXCebksoM+ESu_G_5xksB4p|mo=dWVnN+t%i_>tURTpV7ClSAJOmVOu?bJ2xdh9}6MZ@@o6SRyeMn2cRT<X7I<jR7cS*hON({vzXSh-|PY?jWb$7DvrPS647=Y@jGsAL62W__#VJuRLcCTrYW!ztU~(G51_^km1d1yhVu&nBJS;$1_EM4!hAH(gEIH#UmAQoml@k!qb!g0XSYKfd',
 'test_mark_read_unread.py': 'c-rk*-Hz1A6~6DMD2%jiYiSQdvQjirhXulJR*P7~5^bc}mgVWL9vs}Z*Di;dkdZQo`H?abks?J=l!$0A(lD82)C??;3!cM<J6<6B2>DL=zuP@CEKM#}>5J}m)j6k5ouBWVDq923^#v2wfH$n<|E~kr$^N@Rqwl)|7I2$8Rybhk_)Wgl^R3@-zdEhw<9hcxCb;f;!g8G;<NGXmoX+JA2Ckzot!518SEtejp+_WoXl2A-@TH&2xi3sh9L1M0@fDAE1@9SM*Xdb_wr0RCUT8E<vi4hjARxLQJ&Yc+SEB_MJ&d=bVZ0gb$D8cs1Ns}UzuI}ZAMLPc7vs-f?Zg|=FxqAK8G(3&xe<%EF&#aMMwq_MqJ!vhy!rO334e8=!SK0hiR;YuxT7ktK;K%{DFBpHO!4u>ovz!noaMF>ihk=Sibl5SC!F+2SXf&|jc&VUPwi`R_S(6tA78v?{POB0%qC=uO6c24M-PN=d1^vt^_k;}61C2qUO-Bz&AFzwP?qz4n_=uoHYc>|IOVWpUNQr2Kouxf&@}i;mwSSJWZC?(D?V~Vr+3l!T|e2Z=Ua|YmDhjYVexu2gfH%}lD$~`;?+*H9}O8C`8e7?!Qwm7Q=*LjK<+z;c3=N~C*A@<G@`Fz^oT`IGpAw*k@8fA1s?9xIMM7$;+GHNO_HuFiOu+mC1Acrl4C}eW9=-xFjt+@&0f!-K=+a7jxg<XLRETPnBD7e^ff=^wQQ!p91@eNv|52MebE}2E7rjJE$=B43;`EL*YwOK%eKU-sw}(i@`CLyFC&Dm_`DxrrCSR0=)3;Fbh=zwV9L2mmy|VZC&^E2qsY|@QoNdqZ&z2-8aI*Wps(b;ny{W?^QR%R(c^vQhmH{l?x|*%7*DYt54s3Jde9R0=IKBmp9i5$f)n~QQq!<YCr`AQ^7*HqTrn<v_OZfDrzhjFBv_ZmN<va;{Y=pc`9(bS6}I^LZ-45rTP4mlLJb7cM!X%b$G746T_%BJ58oS%!mEe`8M7DV4_GNXd9e_u_%#LrB`A_k<(eLN@Qm90(rIdor#p=rb^iK~|2(@pq0vJGE5a5Lj@4Q89O1pYz;5L$tSMyelkB^DJNKmih;KymNTMB3?g5LQARWGmw+IL~qkmC=->2}VKYQ_=c>Co(wweY$l4F!46pca9E+HQcJqH_vVErL601Ib{(~p4D2T*S)Gjlsp=1F`9e^hK`TkdQ`8F@!;3g8^SkV-x#)ZUH0B?FO<?t^Aan;}rA2=t}%`p@6OL$n4JiRUT2EYR=2U+s{+pcWK)o<vSjcD7{f#9MQCs*DnxZAeJN*fxGt>6%e=fPDkBMvV5(qHiz_ziZOhq|-@8j>Cp?S4UsNX<#hu2KyYOE-jTYL^4q))r>?@qEZ<$EC*E>5apT6TrFiy3JJ?xs2PA4iAfEN9@rd7ekM~cPx}e6C~m3VMNnqyLZu;<VN~a>(ms>89+H2Nl$j+7!tcwfOyxQ{SSTWcoI~QirY9J6lj39e@-Nc96k#yH77Q&jK)OPXXt^=Ew$;613{1;5tS+HYVTyc^z!I3JhmNpp_2LEH13aN-10(weS|0*#!*;tS8XQ%v0MPkW{a07cUHb)WF*j!}erWaDO_F=g144iSX@5Qx!gZP*_B%!-SWlQ1%FBn>0p+Jqi>ag%PgCnCxo}O>#(l<DcsCT>NB~7uvYHYAf^@l0Rr@JQL%y$C$Np%-v12B}R^H6~Gw?5kakA1AnN8b7y)Tgpf++u}hohj9a3<kn%*B?o<gOTf*Y0t@?B!%U_2Mi%T^WVf1J86yUhUdu5Wua%=e%VJJ}?Z&9Pp+l%Uez-_zJoY&`sGff<XpMRr)cwW)eabqa70;Cf!gINk=)ljEP%m;gX#^u$hWDRc<O=6phh8Wu2o6Pq0bx_>7`t51dr%(K!+vQ<QF|(D?-5D{J5og=$w8A<~bekHaUnaRhF%_nFM~xd9IX;NjV?Lhi4&&%8(A*q(n+ta`jH1vP6;_~U613l758ZCRQ2lMT!2vPqGTB5{zLsRVJZ&kd+3DiFt=&{z`A?BiaYn-fcJZxuiO;(Q0l=6Nk)F4?@5^n0xU-Kx#!=9VP>X&^#CtJ(9SJ~eX&rfBuuZWy#IoF$=?>m#l^+9Kw$yBUFGYMENk%<CUa8rbJ%&j=m*DVzA6Sa(X^H|yGv%2;x4inl88;m|R`##y6<$1d7|_8SPAjk%?zv&?RN-%o}N>q$1tE^DFEMplYOxqp+iNTIEn=rCS8v)nrj@tQeRb4ssBaFjf1>B(elol*$aRq1_<P&@Pn-mO_zF5I{LKwxQvETVhyvg`0pDI>58tG{X_R1Oz6UH?WoDbg+*=b*a>owRt%wwIM!V)9gq;|F8jk_>70Kdz##XXmymE+fO1)yk<@lfm+WAhT$#lOs=hjX?gn4Sa<ibBSPQ1}Y%)O$WX6{0C!aPAo&W1cxqMVIYA>34fJ@5_eVJ#KC!NF{5V+vwSxcs8ZUZlGYss&{+Jh6@wFZCW%PJb+@N<aHe9)<-~b95X*C&fM4ZZj*az{dVSJ^y(EQBg;3A*%|W1a7L{yziYoL;ZjCZRSybhv7J_=rcI6L6V;D>@Cc|0aPT9R;dP$RwFaO3_%AmIJL#~idurv&Nlln#mU)9m}O*@z%o^B#}sb_Q3NiWEVDZMi|+mxjcI^l0Bka0+-KZgngOJ;&LJ9GN<;mcR=BhZ-t5sCOXxf)~X<=P8*Pd1cC?$H9fm8-ml;_<m$3!}-RYlnCykMsgHfd6!3nF&0S)#oDg9eIH^L7Uvq)Nj{A&rq2tm+?Yl-?U)i{DwzWqDRT`lrD`o@*ANOhk;TFK*!JiWA~Q2GSS-AAtu7T42QeY7wZY67vM*0?4q-ke#`E9YD-&=-m@#Q)S+*bOYBCphmG#bT6>gc#Z}Hsw5pyyj$4LvjlX9-mKJ!kdOW`5+ZE<qfr;`PaC+NPSAWxs{c1i|6KEnMYD0<@&6L!P-m)NBk{2)KVqWWZ8r_p;7}}l$n<O`i%uZh$0U`{P5IUeMWpM7Nj|KjYVT?r1GEJlIHum^k$aw2<{1~Tu-0|(Ky|ZrR|Lw{Txm}seiyutqA>r)kcQfyxJNX~C82w}S7zJLcbr5p=?xI={X4762+U4y<{to54dw18<7bnx+n-qmrt$77f7YFja)QjvspC#(2yY5?#Y1=9Iq>%PiNbhm~3kJbo2m',
 'test_move_to_spam.py': 'c-pO4TW=f36@KTh7;k`ZiI^+PX@Ein>)5W67Bv#Xc98-Ku~?ErYMZ@fcQz8^3aAWS2vmRz6ex<KMT$I>HtSfRq{Q}%f5)!;=0DK<gnnmcmt0;%*@*Um+?_e+%(;GNW^6a`L&1dY@{+CI{}B0J{_aPmcIdk-;tu!h*k#%H25+=N`zsz!P8*|fqq&X=Zuo()eJ{%SK2@J*bNR08dq$(1Gu-H&NgKrhkr=U^6Mx1VzmjvGS++QjFK6PL0dET4GMm2FvX!=0#8z*XO7F1RPkJCAd6Ya&PS~sA3QL}*y`-P+C5P!AJAF*A>GrFG)5GL|B?F8<e|3=VCjDf<@HYhU5OYJ8_As3sB|}U<V99ZElJ5O<)kN4`DKR`7wpeF=z&%}q2ikVWpajq^GcCjq_nLmo_Bu5!7VYZKwF>#BtvKmXEUYH8#&CSArMD|`_TKe7AFtjse|P5=W)<0*7Ke^jHzE<*fv(8xHuHQ@pf<SIibyHFyi~5N6y>~EV;DP^&5P}MoN`z)H>`-8Pz8#OX-a&v$pgVYvK{`3FFx{PueBP6eyEHMLfaF%_WEB3EZt7}h{X;o_=}}4UmYZeNuME*C&}R@mhL3ah%)^%h3_~Sy#CWcx(|Y6NI(7Lh$YYRpkfG_@=T@$J|59H(L9mFr;pP;l5S|qXMEEZa9>H)n3>mDEiW(3O->nBt7TH6hp2N;SWY&fYb`FU<~jm>FO2zIHY@DJ#H4H0Y9y>sR9$P+cI~fuOPgVcxG<YmU^Q&V7F}KI_<m=_@jD%)(Cv`7Bdl~^gC1=^bS<yRwH2mazjaI7f;p-_VaB*tZ%XlcCcZYgTBWpsItTqk-Rp|=GF!d^nWYwQvoQ9|Nbo?nn#6dSwRqG-3erbKg?CgA^n^T$9TKeQvrNs>E}OhmW7^%{{^quM>(h@lW_c}{j|IVobe2j<t@=x?GL}Eir?$q{UjOs2b#}kNxkadfMA}Vz>2~@6ksmM#98d7O%P76ZnILm^RsMmMs*{fw;*`Ip8&QFx=yYB&q5zT6%b$DY%G#BBX^uMo`1k*wKb+C%DUuawiwwu=EO~+S9;~qYqZPI^^0ov#N^K<aPy$`@J&NGFbf4gFFZnN}^&?7ZdU=xWq`lKa7?`CyN@A$Wh{hmeKxNb?5{Qx|c9PM}AmT-$^%2ne80z-r5<R8d_vsE^bQB~0PahL5r!S?ZCsJ)p^pgKjrK@NS(g*n8flyeF${!|2BoblWuUsI0XTbEi_xf)?AaIl()H_~esIxMqOdm<LBi$)MY*zxAR1pSJZ|cFNliD)<ZeY0;8DLuR9Y%3W4hup47BL$p$746aGsm-$B5`|pz(^ETC-olF_RxBPOM%tldZAP@9O!VN=cqldM%uL)k;75hS99e?wLT*j9WB#)oRhh_P^nM77cF_eVCN{-<WeI0R)v|85!9!DCug#;pHyN?hi7rljchu0^9$3pY{#^l1Sw+^M}vfX05Bu=gzf07H;n*Tg9Z%1Yn#}|5DJ@)-?Xq>(e(*5xzRO#fBX8qU&F?wC2Q?NyHzWb-0K0#9So@98?g|+SFW=^G9tlx!m`mTK3oSbUq)l4{zyFKN?jWXuT(12vEZA$84GSIbkMcDK}5h4L)xiVegT{x*)=y{@6QBm%0)2c?cBd0Zj^RP!Z^n%V`Z$isbFcNMM)shhahY?6*}8%_?u?icUn9wMo*1r(Yc5SPK+X&QDAw6Xf+)xiV!Xla$dCscTLl?Twboo9yFp8d=py)(4Ap1f-DnZQu-TkT}Wz7IPDGVc{U7lGUU8K7cp!<>oan@eM|^Rc&M;2!*bP@2rVfm0C&gKwDu*!V|TYJXZjLL3F(kO=pO^h9!7fQy`U$7H%HrSA2^MFu<IP)WA8Cp)JrapA^_U8FJm5dYggYTbgM1DE4l%%NkQegKK<EQ7zqvn$DV8)hgmn6F#AnvtL*wAH=(pBPxKaP|1=Qhq!U2Mz1VCB@8YXSUs@6kztzQGxVBse{slo*SPh3))fTTBVT0=MrKN^M$qI;29(w-0W}I1vt|h8%zZpkW8^=fJ<cFw|dSwmsu<nAOH1o{dur3=PoQ0*imlsva!murfJI<y@lp-=$7H@ZEg8vmag>S;6ZZZD!eNpkBMa~S{%I7INfs7s<QyiRis`zYTXHq+#|6)R(JLAmIj(s?<QyyZ3wj}4PTL>|L>jmITwm-T5eL|v6l1C7>U)Z;wsAKB%u9tMF37jLd^Gh%JA$cJI_Ue@@qa1(}>~>cwZhBm7_~933$N^<27s_fs7PaLM3TcsTaB(tucwEmq^>>*$&<L86PH(pX&%|V=8Ag7dq6bG)W}-#0(DJYu&2*YNzTr$u2ktRSBOyEb#L2cY!9Y?G=CDhWiF;Ds%o%iQF|%a}t9Z>4=~CL7mNf$nkTZUtD+Y(xToRFrb-$(6aSmbHCn^pG>MX#)n&06~4#Qg7e0{PrvLuC0W1)c+T5hD(*R*{43{~h+7ce=Y>~!*e2<bfKyW)dWwTPn`Mm0>id=?|D*Q`KoajCf7YomPCC?;4Mj@_8t-OYQN4!6AQ`iPja6ZN&S>>5}GubDu`9e4;Y3k8nP-ameG@Rxd_zSKq1OIeR}J{crKoViB|Yyqh5O2aX#Jg~LEb(t4(57wwG7n`aAE#lCV_d^S5$<#NHX4&w_=)MA0Qwd^Aq;5tDg5=F-cGGaFfFcWRR2L!h*ALLCCnk!`b1Z6FH4SjFt9Ew-`Lde@<ZZEL>T1x?W-xsLCZZaOFgK8yu&uB@M`m5AkUUpeljAhPTZGFZLRa!i8QmWI_|3!Z?8;#J#$fWAU>Znguc{=~%lstFl<Jw?ZQHXPC&Rf6J->|UI`jXanef2',
 'test_reply_with_attachment_from_sent.py': 'c-qxk-EQ2*6~5O~j2R%yZM3xPHbAk-I+0Z+G2%FetuzIc1;Hg}SB$wNL(W>-xCSc2`T;5+0SXjF(ZYo<DtTjDm8~>!FZ>*&bmtdn9--&V@PEl&+15p>3!6*MoH;Y|o$vh2n0?pr7-43g&Y0r)OW(2MXUCuEdQPAC)S|XI=#%LED(x7ad6Rni&r0%M(O2LDRUDU@j_t?&J{3Q!dpZ5SV=J9u+~MMITH70Rn27%vo-5n?0~Z@912b;^Iqm$0fBRfB*|dIfC%WcRol!&89osO)>@=S&E>sDKJI?Facwt2|VF6~|Ajby^2_A>r!EU%2?1!5qxF75X2f<SkJcV}~_&(es!EW$`gzLfX@lJS`96jK#*N=CO_K6(q1-m4?15NhAyT?1hhy<hH``{5gJ|f{3$UY1=P&&cS;pWkUIt<);t-l%O4VyCr{#H%4LL8UcvIJ|<HG2v|N17#)2mer8cMQ|+wWI;-HhwMDah1BFC;o{pq{Z>3SdM1M-FotMY5v-Wi%aTf*DgZ~(R5iFc$U;weCC<1Jl1salle<&W2Hx#EHTZ4|5e)8Obhjr>PhdU`@%wLS6wgd7WcYX(XCU_FX?D@iS4k={1j>%J}#wPJ6o%#>r+^Tw^{_gpGb^7FsDi4O;V*gnom_&U6@STaE7kw)MexY)1p@#_JK37jYZFMJR#ZjOdBTr;_o{tIx{dJ;d4OYKH_sTI1KjB00e^{ux0p1MCsFD^x_XY;TALi%<l@A2R{S{Am|Q%1>pXH;~jqN;d>%~cBzgHAMzeY55i3xLXpI_&^43cO20P1-yksF<KU1SKWTDJ!Yxo$m?^3Wnt*j4fOQ=lfx(h+8z=N6Rvk@xU+9gNd>C%NzDj~k)tF6NF_FT2^Pd#WFjS-{4;bBMniYMJC4(|eUjbMyc>_Au%?C5lHCOAHmdS>))N`C(({g$}u;8m6?fTI1mIPwEj@Q?0ok~q2&0oGO-G&v9c&?SY1!aMYmm~45{Al&4htk*9%)a?GRaZ^ha8_Y9tH8t{D96mQXgy2L&B0(Z2JI4WV5>f(uB>rVoh1hKb+9!25g|XJDg5)OKd?}+XrD1;Fr?_?nHG_*e|+hxdim22C8F5|x3G+0FlNnT!pNk?1*u?S!XUa5A<HlR_NO+vmFaq$2&&!)x5M@Dj-YA;)I(%?f(DYpm|NW<{|~w%ZPIikiWaE$ePm7`7nuUbxUgq(?F+kBU!H5vl<D)=fBg5yZ^l%54E6?=hoIgEU-S$tbkrobk|Az`hvAlrMz@cef<Fp3j(5NuU<zoV`--B}CEONnHE6^D{R8gLz(}4#vja4V&EPvQ8#EgHPsrlljay6jZQkd}!9!q%5lVO{h+&U6+sqmo*#Gv?0~E(S<Yw?AH@NUF(gLjW#_4jw(<TbvM6*WmIBsFSp!~M*vxM{E2IoX%2kh}2R(BVv19|ZfR$@IE#qK@$o`(S2NFPXdxE6O$(NjlU{e}JF&;JG>5I+8P@GK(Y=1WW^Q4b~pKb{7Ui!+k(H%Ld^yhV=o5dwUATM^;cCrnz3TxDY5me%hWT9ZVKflfB@R&S9Sy4tgS>ib%czW3FDdc)TFH(mJAI`<|Uy0qm33)br3jFGMpM2MxW%E38v0Cg(9MPc-}5!v_-Nk_L#{f3Gos-})4l3Hc*5=js!OBvYAwB*GF#RYbOPzboMt3qgqq^w$wu0aGT%Q^nII8=Ujb$;n1(Dm$DZTWrEXz}UIyI|kY0c`f-fHB9ewaM=ZHi7XNMw9aUD?rh+5Fnsm$3C@sTS|o2>nYtu%ShL#K44T8Y#>VzCk;?F9|%O@^OWoF0Ocq1N+o1g=a=#7B)e5uBA5zTDd6bnL1O#&@fR#S=ZD>+zaY@idO5pD<LiwZsCFI8pk8*x`RiywPh-(@Z(##`SF<w<tXrDz!wNHx(uT=sUsY|bPiuAVD3W%Ju0ad}?Mm?lyTW%aFMDdAQ`yPvdX;YG`HIcVtbfUNavJCRT4l|J?d+PKA4TNZ?aZSpew%50`g<&c3At_~B9De;`fU6S-|PDFIovpDtbbo)4W@N0Djq#&wX&&U-duj)b1d4b^*qz4wR5kaXRTe?HyVO<9AgOoc@qa2$1E-%pA2BBs!cLiXoKSOn0qPE!Ar-oF4@fatw~qqTOHVy8%<Kvp#k-3w>ca$J6npzIpytFhI&qRDW)?m$|$Pb`C)<$J}rmo6|jCQj%y*<b{%)%R^a-4W<sV0u{Fl=(bT#S|HdfxWdQ8b{D<n5`A-%>Jw%r1(1`YpdQ!cZ2}UBzLQ)AI8yConyU)=1qu&mnV@7j7e2&KYJw_&&l^w*EydFHlNDtF149YM#%m#oWtb@oeqlSpG*}$_iQS{8r%V;8E5RoimC4>ZzM4+(+#Ig>}L@dDrNQ|MwI~X^Pj`j%>s!%5xusnl!yM96ffh}0LJb(Rqya~E-qv3!EOB*&intsFZ9Jk@GIFPvXq%19GHvAl7IQ@{#M|jfBY*n`$h-Fay%A_Z&a;zqE)DBfSmXR6?d{@nRk#8$QRHat}aQr9S21n<3Wq$54Zb{|WJ&4A)axSds#>Q77Hsy-sDhr_0a>ui)*gru`3U&+$IR|e=(sgpwnD$N6H$|HK%E*z5D^PA8JYhhkM<VNhiNbsyVHkdhHNEZBR(V};BR1swkR<J5sEYyms5r?iMAI)*@=k8wn(5QDg)HR_7^3TkBErUu@({G<T)KfdW^AR99prbUUMv(5B%P$FnQk$B<w@WfX^hlMSs0cc%SITAAP!>PM6m{QlT>nc79}BzM_p^Ec6jWa<@V@38xQ(VW~Y_0rx+@=MFq_;%C@G&ki}+b>KKWaH0A1JNPy)WpE+K$DF!Z&H<Q^W_F3v$vx`;cTVq2^vPbzE_Nb5NUV=XP+t<#7g^-`_?c9s=dD!yx;7L?fC`nRL*M|YV-zV~tGfNg0X0hs9M+7AW&otFNJv|Y4n7WGi#8<K2q~c+RCY!c9NTT>z5;edYv)#)8GYScEpPP|)PVJq41?Vo*xJpgBz~YpccD`#|V44M*2hmCMwA94=@hCm%n`e%k;tIH3L&b9&xex$O3IZpI!E+yF@ygQTwF$D$XDwTlNtvgCjmqOompxNxmc%uwQRozXgvvF0xf~^z@ALj5=jV@?Fcfb~uaWTORm%h@<<QDEpUthnn5k!14|%rAmSkZ`_0*Jj@g)wW$&w=#H$~S=wj(}lnY0zU{!&z&!%2QGiu9W#NnMj#MuR!Mo<$p?Ra5{_B0?7A+Nv$+wRV2@gnDDKO%>WT%Mv@`PXrY<i_?ZzM;7Q7<2N05xpA)js@RJKPDNeZa5mZEQmpBE5oPF3u=0Rm29bf5$AHu+MbgESK&kVy!qP>33{0J$GnzW54yVqE@zhBHb#Wr1I#VDOKF5Oy%oboni|`t_cwDV&3{TWh;VjU)CWNA{##UhZj<4X8@}*<iGW_UKrmq?peM!ck-ycTNQYuJcYb+D3rzh-*ROq^Tg41=biL&aMjLH%ZRyK(UcH_`RM8Uk=0c`wG<O_$$+Jwi=yW(VJgeNH&s_`?G&HP!0NW0Q<f0}RPmm|SmRk>pfV7zu;!_J7Vblb&&ehjaS@R!Dy&xRIN3=@JIZ3wbzyiQenhm^ERQ$B3Se}Q5E&9Uq{|Cd#_d=i-;CfVYbbNM&}jp-|kHxY<7T_xhFrbAlPqqSLbi*yDZP}px0<_##hUFTL+q1>d3@EGvXhVCOAL~b=67Dt7g3}~cN3+nUHa+G*D#;~gXmSse<>uG&@LP+wqQvMQ$1x6VOsgnz2E^m7A)gdroeFgl5!du225UYg>2&nxU(Ia*rt0|O&XS^PiLz8LS)ca`Z6TH__d)K{?qmDRb%U^Ne5#1Kvh`^f?1v<#y>Bt<-#!T_<S@%MXQ#{O|K6wdYr?r8_@ZJ^UoSUXHmS3n;yvBM?G3jZ4up7S+{*jsXu&>kTw63BwuhT{}p9bn2r|tY`Ao@TJlOF(pM6lk1v;9Ba=mM`43>aBu#1(oT7w}S*IG^mH$L8g{xISNga%hy4ZNzJKYDcwEh-c%)7|Z;cHh_<HijiC96i;kx)HIIprgS;AgFimq>f=4*1m&8FGd)nm><(3%vQ@{sp`M?c%dT`%)m(n@&C_<irvIFW9ft(MuT2qjj5w~=#qfv09*m4PK^|dk5Fq#+bUr>f{uhC#T@J6UdZFgu*VX_<%riN$pPQS>6)3=K(Z0*DMB$-llrzl>S9$V>Gw3DZjhwswlo>XufY{6%qWJNHn9>7)%xJ2iF)e!+(wDikWhpw0l-l*o^GvB6^h%K^Y|B<0Lu!MQCDIkKKMDZcb!?wr6Un|IH7nUJZVF1JLR}5~moK%KrTDYdu9P6|6UGh2^+>$I$uCA$_VSs=2L4z_@w&L`h2dbAR{1?NcvkqcJfQ<DmvmNh#f6EpXa^E*ULvPC(G%zv)$HibBn}tV$llA}!7BU9+{^mu-p;peB1-!}rT^q)DvrB|Jb(34rZ_H+#Xh?RiR-Oo?AyR9*ZIo8Td_p9C#_L5?Rbq_1Pr!0)!}8#81J<SYUb6P@D7mvv*R7S8YM17Vxj%t_zETh!pWx}^K1g|N%8|kyo)SnFA+s&Hg#nJCi3Tt6Pr=1Fuz|-pC9^J(;m<%f{QUmsfL9UlCFe2mfRlYG|HDrT)I1h=QjJ<HH+6Vx1VFWOh2kg_738VnF*&qGnHpMK+OC)o;Wfa1wV=)V8q{U#K*LG=!(N+@Edu%ikLs<bbhM5j!55(&)^EKY22;kPjmRHA-sg(QLslMii^>o+<5!x-Z$&<iO<A)c;hFCd(klk*B3Kie(o*wg>*r)tccJfKk?N7FChO9wtG%z',
 'test_mark_read_unread_sent.py': 'c-rk*TaVPp6@KquQ5b34*3upzSt**R!vbM9Q4ot*qK!1$vOL|@gM-`l`VwYBM#`YMNg0Vqk)kL{M6?g-p))WV1{TNzzr%(%{y_F8<U3Wqc6)A1lZRFMp}Spm&Z$%9@|{y<Yv8$l$U<wt8<zb4>%eug|8CIe`|f}R+~$rI4OlvUhtKzX>o?r5PV4!&-o1qhuDf1nxlWMreI_3d=5hxE*U{&fGKNb_2hs+SM<jY=WyD|b`JalpFH9>uiZ5g0iyrTWyk~S>r)NoR&469G+-RI;?RWY>K)fA4j-RqOd$TNloNUI!WIf(Z*4gWa^fy^~v-Ns6-eU0x<1gN9C2R389x?pvfp`yddo0<+bo?aV!}L8C@5fJ*^><e-^p|EE44*qzc#F9ncT@!y=vxaq1%PsfDL%fq({+26v(Q$eu;2QTqLFR-l9N7?g|$W0=(cP2)V?NWZ(h9d>6M$tFK=AMtR$OLBHvazdJy`Sr%E!b&m1=_QS0341*DYPoM~#aWjP<V8ODxeb0VvbQw$5{c{AV!RDogzO@l9XxfileESq0*!%y7E>0R-C*O#01e9H+{<?Y|MSh5li;fqyPvKLEUz1fO);~|41pT@hVSh5;FC(7gx<i7oQ^!E2#$p#4GJ^C8PPgwjsb1H@qDbGb%;9;A_iDpL-zkZmklXP8?Hsgy{2=g^$ju}~wwX^iXTy;t}dp&~!-AA4~p=qZRs?y`3*}Vlv-}ED1%Vzou5izMss}+Q%AGQYOqBXF7%X`WML%>6$YkKCqWn1Brsw}wf!mRBsEFgrg`@A1urMn9B=)3;Fbh=!bWy-~?SCwUKN9HHCQRM1nAzn?zx2vmZjXTJ5&{y(am8@sjxwDYj=<z=DBgY6r?x|*%7|*aC54s3JdeEeM^K_t(&x6P&!ID0W)HLkU$y05neEy4{UpKCP_Nl^5rzhgEBv=>5k|C+IexhiF{34$E3Y&ZTw?B2*-4f?Ap#}nJE!j*~l6&y{hza1>!S@=Y@G2rf#OxLE16ImTUM$2ZevLsu35ujsxuypmJfk+hbeh`S*-oQIoxlF$KQHc2X!IDtim*k5V|5n4M0k&8+1-4FWreJLntl6V>w(Z8@r`KS6KDsNd&uHvNQXzs1_9xE{4WadZ3=Jtvy-eQo3D4V)im&t9D6dMXbgfzgnTsg5^NBH^@qd&ESx4zKLJkfL%pHM%uT7xvt$*2RBUBa>}-!Ra#d^!;GDb?N<Jmj9>w2~fyhVOpxMx-2-GP8ed)aY^EdDitwBZNWeP8|^!x8OTVyY&1w~%U$SKOshKQYHV+K!^QG&BI0cjZ9q#r6g*f-5@5<n3u?PGEkW+1QO2_^xafozv5)FYaVN16x&Quj0?pTZV-6vSVX*m%D%DNMJYdb?EN5adKH3mu7~9Ht6oSPlv_(91IyxLQi66fG8bsAkw+<Sg|zdSG+p|M^V091$kOqVA=77x9{@D=e@k3in27pEBf!<a*?5W@JM5ZBekPlE?eAMbMDnNZi--1pBU2=nP-~MVOv~4+hwPp+#~CFNqN?H%8aCy0?viY1xL=C4eeSkq;7%0uJ@a2`yW_a#{C)Tqx&&&%S}Kh%nu--L8q=M^!7>bZJTd)%A-ve+FC3%$Rc@TfKIZ<X-du9$)|>T#CZbb($UaJ4Pf}FElMwo{w(<<<Fo@Q?(_Yrq)q%;hLt6`;0I0ZWMAuVvVX~<t6|+>0+O%_G46yd|$PW{lSD|$4rE+oXq?a{w<PA_+$kwTj67oO_YVg{UmPE-4xYw;o7{CDYq|NzAIs7%-;cdtnb=A?w36-hEs=5!|9b#1VG@KPRYSt+YADDIP^JhSs@=7hGPzRQxionrwjQadKA#r?iNuYBBv_*NS>)gQrTX|M2QLe*M!sI?k$DW$s-9cD+{4G8PME40&H0bDTL#Hin>W117R%%@e7Kk9dJ_bfKHU)okDv(#oK2<Y*AB(D10MP)M!5>y?zH(Bo?-qcNdR9VfG;t$T2hEK>&2U@Kwb9rS|y`2x{BsJ_wgQ-X>YiT2K729<Q^-39C0n5!{uwINbCl<aB**K-aK>oZN|w`Ouku4yiLU;k?^h!jC_9t^>gIyjEz=+q@+^%vON@*yb}c^8!{i5FtI(?0HT<FbfA}*y_98C}>$Yy+S9~N1k-FIm}~sQ^MZVGPOQBr++kQV4s^kBXa1cY~uG~-2+ghS=abf#^gyY*{Fb#LkANZr<)cYyXZ37ClE9pa|=snXwmwvpR5U6k@+tAy4gzON);zVpi0LmXn_|SQ_*3(BxkvI7=|`;s%A}hs-|7IeALpj(AYYq5UeZyyBMJ^>jd7dSywFFxBMW)(g;~Z_uMtt;hj=OU>8<@$&geI5AV4C?Q&A2eLYTI_xC$#8}LZB1VyJ!o=TB^f6QBgAw6%5tElVQNwEsh$gl;qat_x-u;3^I8|59lJY=O87v!INfLYivmk4%dFw0@S>7XS)_tDrX7t7GS#GwmU7)T&e!e1hx#9fs)aa12$%;=e+S-y=5R3U9nNehqyXe|EMioqE_lSHK9Ew`t1aEfEfHR(JZh~>FXz;Ey_$Hsa}y*}wxf*^%Xg;3A*%|W1a=9Fyu09EKC@2N6EQC-C~8iIPvcI6L6V-!p<%Hb?<57@n8da`%Nmw)>LWl%fxBd(B7urv&NhgwhuU)9m}O*@z%KG;O!8qwyalU~UYQ+i8rp(#osbi&_MAmflue-0H0mdpfgcK+<y!<Vn#fS}+1BNFkcyo_V%b>1t{Q4GZ)e{YuE%~f7T@%UV<g;BZa@*$qdBfUTk;6L4wW&)37^?4Zij<~X$pp`d5_1pE(GgKzZWxUYXH!WB=zf)3`_=!CA(lzy3eg}2xFi<K1==g2J*iEUfOf-3Qh>377!{JEyVnsrF0e-Z`2)(cHTXwrtTiSB;o?eNi#&fM)V%OpwY;;%D+M_fpE{~?7RrNS?+%lYN{2lADu)xXc@%WPOR+w`ICdzNX>HSV!{Y_sbRP(W#Koc2J8&a%jri5nnUI)n{U-guWd9B-NbVnRzXnO)|WNs9hoxZ37L>MR`bl6wQ;M`9i3;Z3!7=fH+nnvCI@A12k@z&$`F-|wf<J(z&Z{5oO+m-KgyE2&<-<!@uz}eAngWf}T@;`1d`p51u3cOV7AmsSnMYSMIr@bh&%iD|mt<AR&?ysb;Y7Tl+Q!1>7ynm^A=~5RW;w9Ou><t2wJ4+4Hw;a>9Q(Q{X?yHDiD*qQ8I=rO'}



import contextlib
import datetime as _dt
import io
import json
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from selenium.common.exceptions import NoSuchElementException, TimeoutException


TESTS = SCRIPT_ORDER[1:]
CONFIG_PATH = APP_DIR / "config.json"
LOG_ROOT = APP_DIR / "logs"
DUMMY_FILES = {
    "dummy_test_attachment.txt": "Limited systems runner test attachment.\n",
    "dummy_reply_attachment.txt": "Limited systems runner reply attachment.\n",
}

BG = "#09111f"
PANEL = "#111d31"
PANEL_2 = "#17253d"
TEXT = "#ecf4ff"
MUTED = "#8fa3bf"
CYAN = "#54d7ff"
GREEN = "#54e6a5"
AMBER = "#ffc857"
RED = "#ff6b7d"

STATUS_TEXT = {
    "pending": ("در انتظار", MUTED),
    "running": ("در حال اجرا", CYAN),
    "success": ("موفق", GREEN),
    "failed": ("ناموفق", RED),
    "skipped": ("رد شد", AMBER),
    "stopped": ("متوقف شد", RED),
}

MISSING_MARKERS = (
    "nosuchelement",
    "timeoutexception",
    "no such element",
    "unable to locate",
    "پیدا نشد",
    "وجود ندارد",
    "وجود نداشت",
    "در دسترس نیست",
    "موجود نیست",
    "خطا: message:",
)


class _SharedBrowser:
    """مرورگر مشترکی که تا پایان تمام سناریوها بسته نمی‌شود."""

    def __init__(self, browser):
        object.__setattr__(self, "_browser", browser)

    def __getattr__(self, name):
        return getattr(self._browser, name)

    def __setattr__(self, name, value):
        setattr(self._browser, name, value)

    def quit(self):
        return None

    def close(self):
        return None


class _SingleChrome:
    def __init__(self, chrome_factory):
        self.chrome_factory = chrome_factory
        self.browser = None
        self.proxy = None
        self.lock = threading.RLock()

    def get(self, *args, **kwargs):
        with self.lock:
            if self.browser is None:
                self.browser = self.chrome_factory(*args, **kwargs)
                self.proxy = _SharedBrowser(self.browser)
            return self.proxy

    def shutdown(self):
        with self.lock:
            browser = self.browser
            self.browser = None
            self.proxy = None
        if browser is not None:
            try:
                browser.quit()
            except Exception:
                pass

    def clear_performance_log(self):
        with self.lock:
            browser = self.browser
        if browser is not None:
            try:
                browser.get_log("performance")
            except Exception:
                pass


class _ScenarioWriter(io.TextIOBase):
    def __init__(self, app, filename, log_path):
        self.app = app
        self.filename = filename
        self.log_path = log_path
        self.parts = []
        self.file = log_path.open("w", encoding="utf-8")

    def write(self, text):
        if not text:
            return 0
        self.parts.append(text)
        self.file.write(text)
        self.file.flush()
        self.app.events.put(("log", self.filename, text))
        return len(text)

    def flush(self):
        if not self.file.closed:
            self.file.flush()

    def close(self):
        if not self.closed:
            super().close()
            self.file.close()

    @property
    def value(self):
        return "".join(self.parts)


def _decode_source(encoded):
    return zlib.decompress(base64.b85decode(encoded)).decode("utf-8")


def _prepare_source(filename, source):
    if filename == "login.py":
        old_check = 'wait.until(EC.url_contains("/nui/"))'
        generic_check = """wait.until(
                lambda active_driver: (
                    "/nui/" in active_driver.current_url
                    or not any(
                        element.is_displayed()
                        for element in active_driver.find_elements(By.XPATH, "//input[@type='password']")
                    )
                )
            )"""
        if old_check not in source:
            raise RuntimeError("بخش تشخیص موفقیت لاگین در منبع داخلی پیدا نشد.")
        source = source.replace(old_check, generic_check, 1)
    else:
        chrome_creation = "driver = webdriver.Chrome(options=chrome_options)"
        if source.count(chrome_creation) != 1:
            raise RuntimeError(f"بخش ساخت مرورگر در {filename} دقیقاً یک‌بار پیدا نشد.")
        source = source.replace(chrome_creation, "driver = __shared_driver__", 1)

    quit_call = "driver.quit()"
    if source.count(quit_call) != 1:
        raise RuntimeError(f"بخش بستن مرورگر در {filename} دقیقاً یک‌بار پیدا نشد.")
    return source.replace(quit_call, "pass  # مرورگر مشترک فقط پس از پایان کل صف بسته می‌شود.", 1)


def _classify(output, error):
    lowered = output.lower()
    missing = any(marker in lowered for marker in MISSING_MARKERS)
    if isinstance(error, (NoSuchElementException, TimeoutException)):
        return "skipped", "گزینه یا قابلیت موردنیاز در سامانه وجود نداشت."
    if error is not None:
        if missing:
            return "skipped", "گزینه یا قابلیت موردنیاز در سامانه وجود نداشت."
        return "failed", f"{type(error).__name__}: {error}"
    if "❌" in output:
        if missing:
            return "skipped", "گزینه یا قابلیت موردنیاز در سامانه وجود نداشت."
        return "failed", "سناریو پیام خطا ثبت کرد."
    return "success", "سناریو کامل شد."


def _safe_log_name(index, filename):
    return f"{index:02d}_{Path(filename).stem}.log"


class LimitedSystemsUI:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.shared_chrome = None
        self.running = False
        self.logs = {filename: "" for _, filename in SCRIPT_ORDER}
        self.log_paths = {}
        self.selected_log = SCRIPT_ORDER[0][1]
        self.test_vars = {}
        self.status_labels = {}
        self.log_buttons = {}
        self.entries = {}

        root.title("Limited Systems Runner v4")
        root.geometry("1220x780")
        root.minsize(1020, 680)
        root.configure(bg=BG)
        self._setup_style()
        self._build_ui()
        self._load_config()
        self._poll_events()
        root.protocol("WM_DELETE_WINDOW", self._close)

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Glass.TFrame", background=PANEL)
        style.configure("Glass2.TFrame", background=PANEL_2)
        style.configure("Title.TLabel", background=BG, foreground=TEXT, font=("Tahoma", 19, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground=MUTED, font=("Tahoma", 10))
        style.configure("Panel.TLabel", background=PANEL, foreground=TEXT, font=("Tahoma", 10))
        style.configure("Muted.TLabel", background=PANEL, foreground=MUTED, font=("Tahoma", 9))
        style.configure("Glass.TEntry", fieldbackground=PANEL_2, foreground=TEXT, insertcolor=TEXT)
        style.configure("Accent.TButton", background=CYAN, foreground="#07111f", font=("Tahoma", 10, "bold"), padding=9)
        style.map("Accent.TButton", background=[("active", "#8be6ff"), ("disabled", "#355168")])
        style.configure("Stop.TButton", background=RED, foreground="white", font=("Tahoma", 10, "bold"), padding=9)
        style.map("Stop.TButton", background=[("active", "#ff8d9b"), ("disabled", "#51303a")])
        style.configure("Glass.TButton", background=PANEL_2, foreground=TEXT, padding=6)
        style.map("Glass.TButton", background=[("active", "#243957")])
        style.configure("Glass.TCheckbutton", background=PANEL, foreground=TEXT, font=("Tahoma", 9))
        style.map("Glass.TCheckbutton", background=[("active", PANEL)])

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 10))
        ttk.Label(header, text="رانر سامانه‌های ناقص", style="Title.TLabel").pack(anchor="e")
        ttk.Label(
            header,
            text="یک ورود، یک پنجره Chrome، اجرای پشت‌سرهم و ردکردن قابلیت‌های ناموجود",
            style="Sub.TLabel",
        ).pack(anchor="e", pady=(2, 0))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 16))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        right = ttk.Frame(body, style="Glass.TFrame", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        left = ttk.Frame(body, style="Glass.TFrame", padding=16)
        left.grid(row=0, column=0, sticky="nsew")

        self._build_config(right)
        self._build_scenarios(right)
        self._build_logs(left)

    def _build_config(self, parent):
        ttk.Label(parent, text="اطلاعات سامانه", style="Panel.TLabel", font=("Tahoma", 12, "bold")).pack(anchor="e")
        fields = [
            ("url", "آدرس سامانه", False),
            ("username", "نام کاربری", False),
            ("password", "رمز عبور", True),
            ("target_email", "ایمیل مقصد", False),
            ("cc_email", "CC (اختیاری)", False),
            ("bcc_email", "BCC (اختیاری)", False),
        ]
        for key, label, secret in fields:
            row = ttk.Frame(parent, style="Glass.TFrame")
            row.pack(fill="x", pady=(8, 0))
            ttk.Label(row, text=label, style="Muted.TLabel").pack(anchor="e")
            entry = ttk.Entry(row, style="Glass.TEntry", justify="right", show="●" if secret else "")
            entry.pack(fill="x", pady=(3, 0), ipady=5)
            self.entries[key] = entry

    def _build_scenarios(self, parent):
        title_row = ttk.Frame(parent, style="Glass.TFrame")
        title_row.pack(fill="x", pady=(16, 6))
        ttk.Label(title_row, text="سناریوها", style="Panel.TLabel", font=("Tahoma", 11, "bold")).pack(side="right")
        ttk.Button(title_row, text="همه", style="Glass.TButton", command=lambda: self._select_all(True)).pack(side="left")
        ttk.Button(title_row, text="هیچ‌کدام", style="Glass.TButton", command=lambda: self._select_all(False)).pack(side="left", padx=5)

        canvas = tk.Canvas(parent, bg=PANEL, highlightthickness=0, height=260)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        holder = ttk.Frame(canvas, style="Glass.TFrame")
        holder.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=holder, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="right", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        login_row = ttk.Frame(holder, style="Glass.TFrame")
        login_row.pack(fill="x", pady=(2, 5))
        ttk.Label(login_row, text="لاگین (همیشه اجرا می‌شود)", style="Panel.TLabel").pack(side="right")
        login_status = ttk.Label(login_row, text=STATUS_TEXT["pending"][0], style="Muted.TLabel")
        login_status.pack(side="left", padx=5)
        self.status_labels["login.py"] = login_status
        ttk.Button(
            login_row,
            text="لاگ",
            style="Glass.TButton",
            command=lambda: self._show_log("login.py"),
        ).pack(side="left")

        for label, filename in TESTS:
            row = ttk.Frame(holder, style="Glass.TFrame")
            row.pack(fill="x", pady=2)
            var = tk.BooleanVar(value=True)
            self.test_vars[filename] = var
            ttk.Checkbutton(row, text=label, variable=var, style="Glass.TCheckbutton").pack(side="right")
            status = ttk.Label(row, text=STATUS_TEXT["pending"][0], style="Muted.TLabel")
            status.pack(side="left", padx=5)
            self.status_labels[filename] = status
            button = ttk.Button(row, text="لاگ", style="Glass.TButton", command=lambda f=filename: self._show_log(f))
            button.pack(side="left")
            self.log_buttons[filename] = button

        action = ttk.Frame(parent, style="Glass.TFrame")
        action.pack(fill="x", pady=(14, 0))
        self.run_button = ttk.Button(action, text="اجرای تست‌ها", style="Accent.TButton", command=self._start)
        self.run_button.pack(side="right", fill="x", expand=True)
        self.stop_button = ttk.Button(action, text="توقف کل", style="Stop.TButton", command=self._stop, state="disabled")
        self.stop_button.pack(side="left", padx=(0, 8))

    def _build_logs(self, parent):
        top = ttk.Frame(parent, style="Glass.TFrame")
        top.pack(fill="x")
        self.log_title = ttk.Label(top, text="لاگ: لاگین", style="Panel.TLabel", font=("Tahoma", 11, "bold"))
        self.log_title.pack(side="right")
        self.log_folder_label = ttk.Label(top, text="", style="Muted.TLabel")
        self.log_folder_label.pack(side="left")

        self.log_text = tk.Text(
            parent,
            bg="#08101c",
            fg=TEXT,
            insertbackground=TEXT,
            selectbackground="#275172",
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=12,
            pady=12,
        )
        self.log_text.pack(fill="both", expand=True, pady=(10, 0))
        self.log_text.tag_configure("success", foreground=GREEN)
        self.log_text.tag_configure("error", foreground=RED)
        self.log_text.tag_configure("skip", foreground=AMBER)
        self.log_text.tag_configure("info", foreground=CYAN)
        self.log_text.configure(state="disabled")

    def _load_config(self):
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        for key, entry in self.entries.items():
            entry.insert(0, str(data.get(key, "")))

    def _select_all(self, selected):
        if self.running:
            return
        for var in self.test_vars.values():
            var.set(selected)

    def _set_controls(self, running):
        self.running = running
        self.run_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")
        for entry in self.entries.values():
            entry.configure(state="disabled" if running else "normal")

    def _start(self):
        values = {key: entry.get().strip() for key, entry in self.entries.items()}
        required = ("url", "username", "password", "target_email")
        if any(not values[key] for key in required):
            messagebox.showwarning("اطلاعات ناقص", "آدرس، نام کاربری، رمز عبور و ایمیل مقصد الزامی‌اند.")
            return

        try:
            old_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if not isinstance(old_config, dict):
                old_config = {}
        except Exception:
            old_config = {}
        old_config.update(values)
        CONFIG_PATH.write_text(json.dumps(old_config, ensure_ascii=False, indent=2), encoding="utf-8")

        selected = {filename for filename, var in self.test_vars.items() if var.get()}
        self.stop_event.clear()
        self.logs = {filename: "" for _, filename in SCRIPT_ORDER}
        stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = LOG_ROOT / stamp
        run_dir.mkdir(parents=True, exist_ok=True)
        self.log_folder_label.configure(text=f"logs/{stamp}")
        self.log_paths = {
            filename: run_dir / _safe_log_name(index, filename)
            for index, (_label, filename) in enumerate(SCRIPT_ORDER, 1)
        }

        self._set_status("login.py", "pending")
        for _label, filename in TESTS:
            if filename in selected:
                self._set_status(filename, "pending")
            else:
                self._set_status(filename, "skipped")
                note = "⏭️ این سناریو در گزینه‌های اجرا انتخاب نشده است.\n"
                self.logs[filename] = note
                self.log_paths[filename].write_text(note, encoding="utf-8")

        self._show_log("login.py")
        self._set_controls(True)
        threading.Thread(target=self._worker, args=(selected,), daemon=True).start()

    def _worker(self, selected):
        original_chrome = webdriver.Chrome
        shared = _SingleChrome(original_chrome)
        self.shared_chrome = shared
        webdriver.Chrome = shared.get
        results = []
        login_ok = False
        if not selected:
            selected = {filename for _label, filename in TESTS}

        try:
            state, detail = self._run_one(0, "لاگین", "login.py")
            results.append(("لاگین", state, detail))
            login_ok = state == "success"
            if not login_ok:
                for label, filename in TESTS:
                    if filename in selected:
                        self.events.put(("status", filename, "skipped", "به‌دلیل ناموفق‌بودن لاگین اجرا نشد."))
                return

            for index, (label, filename) in enumerate(TESTS, 1):
                if filename not in selected:
                    results.append((label, "skipped", "انتخاب نشده بود."))
                    continue
                if self.stop_event.is_set():
                    self.events.put(("status", filename, "stopped", "اجرای کل مجموعه متوقف شد."))
                    results.append((label, "stopped", "توقف کاربر"))
                    continue
                shared.clear_performance_log()
                state, detail = self._run_one(index, label, filename)
                results.append((label, state, detail))
        except BaseException as exc:
            detail = f"خطای داخلی رانر: {type(exc).__name__}: {exc}"
            results.append(("رانر", "failed", detail))
            self.events.put(("runner_error", detail, traceback.format_exc()))
        finally:
            webdriver.Chrome = original_chrome
            shared.shutdown()
            self.shared_chrome = None
            self.events.put(("finished", results, self.stop_event.is_set()))

    def _run_one(self, index, label, filename):
        self.events.put(("status", filename, "running", ""))
        self.events.put(("select_log", filename, label))
        writer = _ScenarioWriter(self, filename, self.log_paths[filename])
        error = None
        try:
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                print("=" * 72)
                print(f"▶ شروع: {label}")
                print("=" * 72)
                source = _prepare_source(filename, _decode_source(SOURCES[filename]))
                namespace = {
                    "__name__": "__main__",
                    "__file__": str(APP_DIR / filename),
                    "__package__": None,
                    "__cached__": None,
                    "__shared_driver__": self.shared_chrome.proxy if self.shared_chrome else None,
                }
                exec(compile(source, filename, "exec"), namespace, namespace)
                print(f"\n✓ پایان: {label}")
        except BaseException as exc:
            error = exc
            with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
                traceback.print_exc()
        finally:
            output = writer.value
            writer.close()

        if self.stop_event.is_set():
            state, detail = "stopped", "اجرای کل مجموعه توسط کاربر متوقف شد."
        else:
            state, detail = _classify(output, error)
        self.events.put(("status", filename, state, detail))
        return state, detail

    def _stop(self):
        if not self.running:
            return
        self.stop_event.set()
        self.stop_button.configure(state="disabled")
        self._append_visible("\n⏹️ درخواست توقف کل سناریوها ثبت شد.\n", "error")
        shared = self.shared_chrome
        if shared is not None:
            threading.Thread(target=shared.shutdown, daemon=True).start()

    def _set_status(self, filename, state, detail=""):
        label = self.status_labels.get(filename)
        if label is not None:
            text, color = STATUS_TEXT[state]
            label.configure(text=text, foreground=color)

    def _show_log(self, filename, label=None):
        self.selected_log = filename
        if label is None:
            label = next((name for name, item in SCRIPT_ORDER if item == filename), filename)
        self.log_title.configure(text=f"لاگ: {label}")
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", self.logs.get(filename, ""))
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def _append_visible(self, text, tag=None):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text, tag or "")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    _, filename, text = event
                    self.logs[filename] += text
                    if self.selected_log == filename:
                        if "❌" in text:
                            tag = "error"
                        elif "⏭" in text or "⚠" in text:
                            tag = "skip"
                        elif "✓" in text or "✅" in text:
                            tag = "success"
                        elif "ℹ" in text or "▶" in text:
                            tag = "info"
                        else:
                            tag = None
                        self._append_visible(text, tag)
                elif kind == "status":
                    _, filename, state, detail = event
                    self._set_status(filename, state, detail)
                    if detail:
                        note = f"\n[{STATUS_TEXT[state][0]}] {detail}\n"
                        self.logs[filename] += note
                        path = self.log_paths.get(filename)
                        if path is not None:
                            with path.open("a", encoding="utf-8") as log_file:
                                log_file.write(note)
                        if self.selected_log == filename:
                            self._append_visible(note, "error" if state in ("failed", "stopped") else "skip")
                elif kind == "select_log":
                    _, filename, label = event
                    self._show_log(filename, label)
                elif kind == "runner_error":
                    _, detail, trace = event
                    self._append_visible(f"\n❌ {detail}\n{trace}\n", "error")
                    messagebox.showerror("خطای داخلی رانر", detail)
                elif kind == "finished":
                    _, results, stopped = event
                    self._set_controls(False)
                    if stopped:
                        messagebox.showinfo("توقف اجرا", "اجرای کل سناریوها متوقف شد.")
                    else:
                        success = sum(state == "success" for _label, state, _detail in results)
                        failed = sum(state == "failed" for _label, state, _detail in results)
                        skipped = sum(state == "skipped" for _label, state, _detail in results)
                        messagebox.showinfo(
                            "پایان اجرا",
                            f"اجرا تمام شد.\nموفق: {success}\nناموفق: {failed}\nردشده: {skipped}",
                        )
        except queue.Empty:
            pass
        self.root.after(100, self._poll_events)

    def _close(self):
        if self.running:
            if not messagebox.askyesno("خروج", "تست‌ها در حال اجرا هستند. کل اجرا متوقف و برنامه بسته شود؟"):
                return
            self._stop()
        self.root.destroy()


def main():
    LOG_ROOT.mkdir(exist_ok=True)
    for filename, content in DUMMY_FILES.items():
        path = APP_DIR / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    root = tk.Tk()
    LimitedSystemsUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
