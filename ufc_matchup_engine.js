(function(root){'use strict';
function clamp(x,a,b){return Math.max(a,Math.min(b,x))}
function logit(p){return Math.log(p/(1-p))}
function logistic(x){return 1/(1+Math.exp(-x))}
function metrics(profile){const t=profile?.career_round_totals,n=t?.round_rows;if(!Number.isFinite(n)||n<1)return null;return {rounds:n,sig:t.sig_landed/n,sigAttempts:t.sig_attempted/n,td:t.td_landed/n,tdAttempts:t.td_attempted/n,control:t.control_seconds/n,sub:t.submission_attempts/n,sigAccuracy:t.sig_attempted>0?t.sig_landed/t.sig_attempted:0,tdAccuracy:t.td_attempted>0?t.td_landed/t.td_attempted:0}}
function estimate(red,blue,elo,unified){
 const a=metrics(red),b=metrics(blue);
 if(!a||!b)return {status:'INSUFFICIENT_DATA',reason:'Both fighters need matched round-level histories'};
 const n=Math.min(a.rounds,b.rounds),reliability=clamp(n/(n+12),0,0.85);
 const eloValid=Number.isFinite(elo?.red_elo)&&Number.isFinite(elo?.blue_elo);
 const eloLogOdds=eloValid?clamp((elo.red_elo-elo.blue_elo)*Math.LN10/400,-2,2):0;
 // Shrunk matchup features: capped to limit small-sample outliers. These are transparent heuristic weights, not fitted coefficients.
 const strike=clamp((a.sig-b.sig)/12,-1,1);
 const accuracy=clamp((a.sigAccuracy-b.sigAccuracy)/0.20,-1,1);
 const takedown=clamp((a.td-b.td)/1.5,-1,1);
 const control=clamp((a.control-b.control)/90,-1,1);
 const sub=clamp((a.sub-b.sub)/0.8,-1,1);
 const statsLogOdds=reliability*(0.35*strike+0.18*accuracy+0.28*takedown+0.12*control+0.07*sub);
 const base=eloValid?0.75*eloLogOdds:0;
 const p=clamp(logistic(base+statsLogOdds),0.10,0.90);
 const width=clamp(0.12+0.36/(Math.sqrt(n)+1)+(eloValid?0:0.12),0.12,0.40);
 return {status:'EXPLORATORY',red_probability:p,blue_probability:1-p,red_range:[clamp(p-width,0.01,0.99),clamp(p+width,0.01,0.99)],winner:p>=0.5?'red':'blue',min_round_rows:n,elo_available:eloValid,components:{elo:base,striking:reliability*(0.35*strike+0.18*accuracy),grappling:reliability*(0.28*takedown+0.12*control+0.07*sub)},note:'Heuristic independent matchup estimate; weights and ranges are not trained or calibrated. Never interpret as verified betting EV.'}
}
root.KennyUfcMatchup={estimate,metrics};
})(typeof window!=='undefined'?window:globalThis);
