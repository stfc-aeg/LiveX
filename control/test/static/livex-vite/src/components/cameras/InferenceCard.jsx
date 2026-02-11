import React from 'react';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import { useAdapterEndpoint, WithEndpoint, TitleCard } from 'odin-react';
import { FloatingLabel } from 'react-bootstrap';
import Button from 'react-bootstrap/Button';
import { useState } from 'react';
import MonitorGraph from '../furnace/MonitorGraph';

import { checkNull, checkNullNoDp, floatingInputStyle, floatingLabelStyle } from '../../utils';

const EndPointButton = WithEndpoint(Button);

function InferenceCard(props) {
    const {endpoint_url} = props;
    const {name} = props;
 
    const inferenceEndPoint = useAdapterEndpoint('inference', endpoint_url, 1000);
    const inferenceResults = inferenceEndPoint?.data[name]?.results;

    const sampleRate = React.useMemo(() => inferenceResults?.frames_per_second );

    const [flatfieldNum, setFlatfieldNum] = useState(0);
    const handleFlatfieldNumChange = (e) => {
      setFlatfieldNum(e.target.value);
    };

    const fullpaths = React.useMemo(() => [
      `${name}/probabilities/columnar`,
      `${name}/probabilities/equiaxed`,
      `${name}/probabilities/alpha`,
      `${name}/probabilities/beta`,
      `${name}/probabilities/hot_tear`
    ], [name])

    return (

        <TitleCard title={`${name} Inference Details`}>
          <Row className='mb-3'>
            <Col>
              <Row className="mb-3">
                <Col xs={4}>
                  <FloatingLabel label="# Predictions">
                    <Form.Control
                      plaintext
                      readOnly
                      style={floatingLabelStyle}
                      value={checkNullNoDp(inferenceResults?.num_predictions)}
                    />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                  <FloatingLabel label="Last Frame #">
                    <Form.Control
                      plaintext
                      readOnly
                      style={floatingLabelStyle}
                      value={checkNullNoDp(inferenceResults?.last_frame_number)}
                    />
                  </FloatingLabel>
                </Col>
                <Col xs={4}>
                <FloatingLabel label="Avg Inf. Time">
                  <Form.Control
                    plaintext
                    readOnly
                    style={floatingLabelStyle}
                    value={checkNull(inferenceResults?.avg_inference_time_ms)}
                  />
                </FloatingLabel>
                </Col>
              </Row>
              <Row className='mt-3'>
                  <Col xs={3}/>
                  <Col>
                    <FloatingLabel label="Flatfield Acquisition #">
                      <Form.Control
                        style={floatingInputStyle}
                        type="number"
                        value={inferenceResults?.ff_correction_file}
                        onChange={handleFlatfieldNumChange}
                      />
                    </FloatingLabel>
                  </Col>
                  <Col>
                    <Row>
                      <EndPointButton
                        endpoint={inferenceEndPoint}
                        fullpath={`${name}/results/set_flatfield_num`}
                        value={flatfieldNum}>
                        Set flatfield from acquisition
                      </EndPointButton>
                    </Row>
                  <Row>
                    <EndPointButton
                      endpoint={inferenceEndPoint}
                      fullpath={`${name}/results/set_flatfield_num`}
                      value={-1 /*Special case adapter-side,*/} 
                      variant='danger'
                    >
                        Clear flatfield
                    </EndPointButton>
                  </Row>
                </Col>
              </Row>
              <Row className="mt-3 justify-content-center">
                <Col xs={0} sm={1} md={2}/>
                <Col>
                  <FloatingLabel label="Active classes">
                    <Form.Control
                      readOnly
                      plaintext
                      value={inferenceEndPoint?.data?.[name]?.results?.active_classes}
                      style={{
                          border: '1px solid lightgreen',
                          backgroundColor: '#e0ffe2ff',
                          borderRadius: '0.375rem'
                      }}
                    />
                  </FloatingLabel>
                </Col>
                <Col xs={0} sm={1} md={2}/>
              </Row>
            </Col>
          </Row>
          <Row>
            <MonitorGraph
              endpoint={inferenceEndPoint}
              paths={fullpaths}
              seriesNames={['col', 'equi', 'alpha', 'beta', 'tear']}
              xSampleRate={sampleRate}
              xLabel="Time (s)"
            />
          </Row>
        </TitleCard>
    )
}

export default InferenceCard;

