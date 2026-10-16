SELECT *
From Projects.dbo.CovidDeaths
where continent is not null
order by 3,4

Select *
From Projects.dbo.CovidVaccination
order by 3,4

-- Select data that we are going be using

--Select Location,date, total_cases, new_cases, total_deaths, population
--From Projects. dbo.CovidDeaths



-- Looking at Total Cases vs Total Deaths
-- shows likelihood of dying if you contract covid in your country
select continent, date, total_cases, total_deaths,(total_deaths/total_cases)*100 as DeathPercentage
from Projects. dbo.CovidDeaths
order by continent desc


-- Looing at Total_cases vs population
-- shows what percentage of population has Coivd
select Location, date, total_cases, population,(total_cases/population)*100 as percentpopulationinfected
from Projects. dbo.CovidDeaths
where location like '%states%'
order by 1,2


-- Looking at Countries with Highest Infection Rate compared to Population

select Location, population, MAX(total_cases) as Highestinfectioncount, Max(total_cases/population)*100 as percentpopulationinfected
from Projects. dbo.CovidDeaths
-- where location like '%states%'
Group by Location, population
order by percentpopulationinfected desc


-- Showing Countries with Highest Death Count per Population

select Location, Max(cast(Total_deaths as int)) as TotalDeathCount 
from Projects. dbo.CovidDeaths
-- where location like '%states%'
where continent is not null
Group by Location
order by TotalDeathCount desc

-- Breaking things down by Continent

select continent, Max(cast(Total_deaths as int)) as TotalDeathCount 
from Projects. dbo.CovidDeaths
-- where location like '%states%'
where continent is null
Group by continent
order by TotalDeathCount desc 


-- Breaking things down by Continent


-- Showing continents with the highest death count per population

select continent, Max(cast(Total_deaths as int)) as TotalDeathCount 
from Projects. dbo.CovidDeaths
-- where location like '%states%'
where continent is null
Group by continent
order by TotalDeathCount desc 




-- Global Numbers

select date, sum(new_cases) as total_cases, sum(cast(new_deaths as int)) as total_deaths, sum(cast(new_deaths as int))/sum(new_cases)*100 as DeathPercentage
from Projects.dbo.CovidDeaths 
-- where location like 
where continent is not null
group by date
order by 1,2



select sum(new_cases) as total_cases, sum(cast(new_deaths as int)) as total_deaths, sum(cast(new_deaths as int))/sum(new_cases)*100 as DeathPercentage
from Projects.dbo.CovidDeaths 
-- where location like 
where continent is not null
-- group by date
order by 1,2




-- Looking at total population vs Vaccination

select dea.continent, dea. location, dea.date, dea.population, vac.new_vaccinations, sum(cast(new_vaccinations as int)) over (Partition by dea.location order by dea.location,
dea.date) as RollingPeopleVaccinated, (RollingPeopleVaccinated/population) * 100
from Projects. dbo.CovidDeaths dea
join Projects. dbo.CovidVaccination vac
	on dea.location = vac.location
	and dea.date = vac.date
where dea.continent is not null
order by 2,3


-- USE CTE

with PopvsVac (Continent, location, date, population, new_vaccinations, RollingPeopleVaccinated)
as 
(
select dea.continent, dea. location, dea.date, dea.population, vac.new_vaccinations, sum(cast(new_vaccinations as int)) over (Partition by dea.location order by dea.location,
dea.date) as RollingPeopleVaccinated --,(RollingPeopleVaccinated/population) * 100
from Projects. dbo.CovidDeaths dea
join Projects. dbo.CovidVaccination vac
	on dea.location = vac.location
	and dea.date = vac.date
where dea.continent is not null
-- order by 2,3
)
select* , (RollingPeopleVaccinated/population) * 100
from PopvsVac



-- temp table

drop table if exists #PercentPopulationVaccinated
create table #PercentPopulationVaccinated
(
continent nvarchar(255),
Location nvarchar(255),
date datetime,
population numeric, 
New_vaccinations numeric,
Rollingpeoplevaccinated numeric
)


insert into #PercentPopulationVaccinated
select dea.continent, dea. location, dea.date, dea.population, vac.new_vaccinations, sum(cast(new_vaccinations as bigint)) over (Partition by dea.location order by dea.location,
dea.date) as RollingPeopleVaccinated --,(RollingPeopleVaccinated/population) * 100
from Projects. dbo.CovidDeaths dea
join Projects. dbo.CovidVaccination vac
	on dea.location = vac.location
	and dea.date = vac.date
where dea.continent is not null
order by 2,3

select * , (RollingPeopleVaccinated/population) * 100
from #PercentPopulationVaccinated 


-- Creating View to store data for visualizations

create View PercentPopulationVaccinated as 
select dea.continent, dea. location, dea.date, dea.population, vac.new_vaccinations, sum(cast(new_vaccinations as bigint)) over (Partition by dea.location order by dea.location,
dea.date) as RollingPeopleVaccinated --,(RollingPeopleVaccinated/population) * 100
from Projects. dbo.CovidDeaths dea
join Projects. dbo.CovidVaccination vac
	on dea.location = vac.location
	and dea.date = vac.date
where dea.continent is not null
--order by 2,3

SELECT *
FROM PercentPopulationVaccinated