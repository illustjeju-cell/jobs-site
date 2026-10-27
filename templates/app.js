const $=s=>document.querySelector(s);let D=[],N=30;
function lab(x){return x.dd===null?"상시":x.dd===0?"오늘 마감":"D-"+x.dd}
function render(){const q=$("#q").value.trim(),f=$("#f").value,r=$("#r").value,t=$("#t").value,ed=$("#ed").value,c=$("#c").value,d=$("#d").value;
const L=D.filter(x=>(!q||(x.org+x.title).includes(q))&&(!f||x.fields.includes(f))&&(!r||x.regions.includes(r)||x.regions.includes("전국"))&&(!t||x.emp===t)&&(!ed||x.eduL===ed)&&(!c||x.car===c||x.car==="신입·경력")&&(!d||(x.dd!==null&&x.dd<=+d)));
$("#cnt").textContent=L.length.toLocaleString()+"건";$("#more").style.display=L.length>N?"block":"none";
$("#list").innerHTML=L.slice(0,N).map((x,i)=>`<a class="card" href="j/${x.id}.html"><div class="meta"><span class="st ${x.dd!==null&&x.dd<=3?"urgent":""}">${lab(x)}</span><span>${x.regions.join(", ")}</span></div><p class="org">${x.org}</p><h2>${x.title}</h2><p class="sub">${x.fields.join(", ")} · ${x.emp} · ${x.eduL}${x.salary?" · <b>"+x.salary+"</b>":""}</p></a>`+"").join("")}
["#q","#f","#r","#t","#ed","#c","#d"].forEach(s=>$(s).addEventListener("input",()=>{N=30;render()}));$("#more").onclick=()=>{N+=30;render()};
fetch("data.json").then(r=>r.json()).then(d=>{D=d;render()});
