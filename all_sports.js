/* Sports Model Lab market registry. No invented player records or odds.
   New sports show empty-state until verified provider adapters exist. */
const sportMarkets = {
  "NCAA Football": {"Passing yards":[100,150,200,250,300,350,400],"Rushing yards":[10,25,40,50,75,100,125,150],"Receiving yards":[10,25,40,50,60,75,100],"Receptions":[1,2,3,4,5,6,7],"Touchdowns":[1,2,3],"Completions":[10,15,20,25,30],"Pass attempts":[15,20,25,30,35,40]},
  "WNBA": {"Points":[5,10,15,20,25,30],"Rebounds":[2,4,6,8,10,12],"Assists":[2,4,6,8,10],"Threes":[1,2,3,4,5],"PRA":[10,15,20,25,30,35]},
  "International Basketball": {"Points":[5,10,15,20,25,30],"Rebounds":[2,4,6,8,10],"Assists":[2,4,6,8,10],"PRA":[10,15,20,25,30,35]},
  "MLB": {"Hits":[1,2,3,4],"Total bases":[1,2,3,4,5],"Strikeouts":[2,4,6,8,10,12],"RBIs":[1,2,3],"Runs":[1,2,3],"Home runs":[1,2]},
  "International Baseball": {"Team runs":[1,2,3,4,5,6,7],"Game total runs":[5,6,7,8,9,10]},
  "NHL": {"Shots on goal":[1,2,3,4,5,6],"Points":[1,2,3],"Goals":[1,2],"Assists":[1,2,3],"Saves":[15,20,25,30,35]},
  "International Hockey": {"Shots on goal":[1,2,3,4,5],"Points":[1,2,3],"Goals":[1,2],"Assists":[1,2],"Saves":[15,20,25,30]},
  "NCAA Hockey": {"Team goals":[1,2,3,4,5],"Game total goals":[3,4,5,6,7]},
  "Tennis": {"Match winner":[1],"Sets won":[1,2,3],"Aces":[2,4,6,8,10],"Games won":[6,8,10,12,15]},
  "UFC": {"Significant strikes":[10,25,50,75,100],"Takedowns":[1,2,3,4,5],"Fight duration minutes":[5,10,15,20],"Knockdowns":[1,2]},
  "DWCS": {"Significant strikes":[10,25,50,75,100],"Takedowns":[1,2,3,4,5],"Fight duration minutes":[5,10,15]},
  "PFL": {"Moneyline win":[1]},
  "Table Tennis": {"Moneyline win":[1]},
  "Esports CS2": {"Moneyline win":[1]},
  "Esports Valorant": {"Moneyline win":[1]},
  "Esports LoL": {"Moneyline win":[1]},
  "Esports Dota 2": {"Moneyline win":[1]}
};
for (const [sport,markets] of Object.entries(sportMarkets)) {
  config[sport] = {markets:Object.fromEntries(Object.entries(markets).map(([name,lines])=>[name,{lines,players:[]}]))};
  $('sport').append(new Option(sport,sport));
}
const previousRender = render;
render = function() {
  previousRender();
  const body=$('tbody');
  if (!body.children.length) {
    const row=document.createElement('tr');
    const cell=document.createElement('td');
    cell.colSpan=data().lines.length+2;
    cell.style.cssText='padding:36px 16px;color:#b7c9b8;text-align:center;white-space:normal';
    cell.textContent='UNAVAILABLE — no verified player-game logs or market projections are connected for this selection. No example hit rates are generated.';
    row.append(cell);body.append(row);
  }
};
resetMarket();
