import React from 'react';
import PiezoStage from './PiezoStage.jsx';

function KimController(props) {
  const {name, motors, kinesisEndPoint} = props;
  
  return (
    <div className="controller">
      Controller: {name}
      {Object.entries(motors).map(([motorName, motorData]) => (
        <PiezoStage
          key={motorName}
          name={motorName}
          data={motorData}
          kinesisEndPoint={kinesisEndPoint}
          dataPath={`controllers/${name}/motors/${motorName}`}
        />
      ))}
    </div>
  );
}

export default KimController;