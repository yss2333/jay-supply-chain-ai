
Select * 
from Projects. dbo.NashvilleHousing

-------------------------------------------------------------------------

----- Standardize Date Format

-- convert SaleDate column to date format
Select SaleDateConverted, convert(date,SaleDate)
from Projects. dbo.NashvilleHousing

update NashvilleHousing
SET SaleDate = Convert(Date,SaleDate)

-- shows minute in the column, so make the column not showing minutes
Alter Table NashvilleHousing
Add SaleDateConverted Date; 

update NashvilleHousing
SET SaleDateConverted = Convert(Date,SaleDate)



---------------------------------

--Populate Property Address Data

Select *
from Projects. dbo.NashvilleHousing
--Where PropertyAddress is null
order by ParcelID


-- Populate Property Address that has already been used with the same ParcelID
Select a.ParcelID, a.PropertyAddress, b.ParcelID, b.PropertyAddress, ISNULL(a.propertyAddress, b.PropertyAddress)
from Projects. dbo.NashvilleHousing a
Join Projects. dbo.NashvilleHousing b
	on a.ParcelID = b.ParcelID
	AND a.[UniqueID] <> b.[UniqueID]
Where a.PropertyAddress is null



update a
SET PropertyAddress = ISNULL(a.propertyAddress, b.PropertyAddress)
from Projects. dbo.NashvilleHousing a
Join Projects. dbo.NashvilleHousing b
	on a.ParcelID = b.ParcelID
	AND a.[UniqueID] <> b.[UniqueID]
Where a.PropertyAddress is null



---------------------------------------------------------------------

--Dividing Address into Individual Column (Address, City, State)

Select PropertyAddress
from Projects. dbo.NashvilleHousing


Select 
SUBSTRING(PropertyAddress,1,CHARINDEX(',',PropertyAddress) -1) as Address,
SUBSTRING(PropertyAddress,CHARINDEX(',',PropertyAddress) +1, LEN(PropertyAddress)) as Address 
from Projects. dbo.NashvilleHousing


Alter Table NashvilleHousing
Add PropertySplitAddress Nvarchar(255); 

update NashvilleHousing
SET PropertySplitAddress = SUBSTRING(PropertyAddress,1,CHARINDEX(',',PropertyAddress) -1)

Alter Table NashvilleHousing
Add PropertySplitcity Nvarchar(255); 

update NashvilleHousing
SET PropertySplitcity = SUBSTRING(PropertyAddress,CHARINDEX(',',PropertyAddress) +1, LEN(PropertyAddress))




-- Run Updated Dataset
Select *
from Projects.dbo.NashvilleHousing



-- Break down owner address into address, city, and state
Select OwnerAddress
from Projects.dbo.NashvilleHousing


select
PARSENAME(Replace(OwnerAddress,',','.'),3),
PARSENAME(Replace(OwnerAddress,',','.'),2),
PARSENAME(Replace(OwnerAddress,',','.'),1)
FROM projects.dbo.NashvilleHousing

-- Update address
Alter Table NashvilleHousing
Add OwnerSplitAddress Nvarchar(255); 

update NashvilleHousing
SET OwnerSplitAddress = PARSENAME(Replace(OwnerAddress,',','.'),3)

-- Update City
Alter Table NashvilleHousing
Add OwnerSplitCity Nvarchar(255); 

update NashvilleHousing
SET OwnerSplitCity = PARSENAME(Replace(OwnerAddress,',','.'),2)


--Update State
Alter Table NashvilleHousing
Add OwnerSplitState Nvarchar(255); 

update NashvilleHousing
SET OwnerSplitState = PARSENAME(Replace(OwnerAddress,',','.'),1)


select * 
from Projects.dbo.NashvilleHousing


---------------------------------------------

-- Change Y and N to Yes and No in "Sold as Vacant" field



select Distinct(SoldAsVacant), count(SoldAsVacant)
from Projects.dbo.NashvilleHousing
Group by SoldAsVacant
order by 2

-- if else statment for Yes and No
select SoldAsVacant
,case when SoldAsVacant = 'Y' Then 'Yes'
	  when SoldAsVacant = 'N' then 'No'
	  Else SoldAsVacant
	  END
from Projects.dbo.NashvilleHousing



Update NashvilleHousing
SET SoldAsVacant = CASE when SoldAsVacant = 'Y' Then 'Yes'
	When SoldAsVacant = 'N' Then 'No'
	Else SoldAsVacant
	END



------------------------------------------------------------------------------

-- Remove Duplicates

-- Using CTE

WITH RowNumCTE AS(
Select *,
	ROW_number() Over (
	PARTITION BY ParcelID, 
				 PropertyAddress,
				 SalePrice,
				 SaleDate,
				 LegalReference
				 Order by 
					UniqueID
					) row_num
from Projects.dbo.NashvilleHousing
-- order by ParcelID
)

SELECT * 
from RowNumCTE
where row_num >1
-- order by PropertyAddress






------------------------------------------------------------------


-- Delete Unused Columns

Select *
from Projects.dbo.NashvilleHousing

Alter Table Projects.dbo.NashvilleHousing
-DROP COLUMN PropertyAddress, OwnerAddress, TaxDistrict
Drop Column SaleDate




